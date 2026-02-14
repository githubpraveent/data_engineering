# Databricks notebook source
# MAGIC %md
# MAGIC # ML Training Pipeline: Sentiment Classification Model
# MAGIC 
# MAGIC This notebook trains a sentiment classification model using Gold layer data.
# MAGIC 
# MAGIC **Model**: Text classification for customer reviews
# MAGIC **Training Data**: Gold aggregated customer reviews with labels
# MAGIC **Framework**: MLflow + Spark ML / Transformers

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import json
import mlflow
import mlflow.spark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, regexp_replace, lower, trim
from pyspark.ml import Pipeline
from pyspark.ml.feature import Tokenizer, StopWordsRemover, CountVectorizer, IDF
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
import pandas as pd

# Load configuration
workspace_config_path = "/Workspace/Shared/lakehouse/config/workspace_config.json"
with open(workspace_config_path, 'r') as f:
    ws_config = json.load(f)

catalog = ws_config["workspace"]["catalog"]
gold_sentiment_table = f"{catalog}.gold.sentiment_summary"
silver_table = f"{catalog}.silver.customer_events_cleaned"

# MLflow settings
mlflow.set_experiment("/Shared/lakehouse/sentiment_classification")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prepare Training Data

# COMMAND ----------

def prepare_training_data():
    """
    Prepare training data from Silver layer reviews.
    Creates labels from ratings (positive if rating >= 4, negative if <= 2).
    """
    
    # Read review data from Silver
    df_reviews = (
        spark.table(silver_table)
        .filter(
            (col("is_review") == True) &
            (col("text_content") != "") &
            (col("text_content").isNotNull()) &
            (col("rating").isNotNull()) &
            (col("rating") > 0)
        )
        .select(
            "event_id",
            "text_content",
            "rating",
            "customer_id",
            "product_id",
            "category"
        )
    )
    
    # Clean text
    df_cleaned = (
        df_reviews
        .withColumn("text_cleaned", 
                   trim(lower(regexp_replace(col("text_content"), "[^a-zA-Z\\s]", ""))))
        .filter(col("text_cleaned") != "")
        .filter(length(col("text_cleaned")) >= 10)  # Minimum length
    )
    
    # Create labels: 1 for positive (rating >= 4), 0 for negative (rating <= 2), exclude neutral
    df_labeled = (
        df_cleaned
        .withColumn(
            "label",
            when(col("rating") >= 4, 1.0)
            .when(col("rating") <= 2, 0.0)
            .otherwise(None)
        )
        .filter(col("label").isNotNull())
    )
    
    # Split into train/test
    train_df, test_df = df_labeled.randomSplit([0.8, 0.2], seed=42)
    
    print(f"Training samples: {train_df.count()}")
    print(f"Test samples: {test_df.count()}")
    print(f"Positive samples: {train_df.filter(col('label') == 1.0).count()}")
    print(f"Negative samples: {train_df.filter(col('label') == 0.0).count()}")
    
    return train_df, test_df

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature Engineering

# COMMAND ----------

def create_feature_pipeline():
    """
    Create ML pipeline for text feature extraction.
    """
    # Tokenize text
    tokenizer = Tokenizer(
        inputCol="text_cleaned",
        outputCol="tokens"
    )
    
    # Remove stop words
    stopwords_remover = StopWordsRemover(
        inputCol="tokens",
        outputCol="filtered_tokens"
    )
    
    # Count vectorizer (TF)
    count_vectorizer = CountVectorizer(
        inputCol="filtered_tokens",
        outputCol="raw_features",
        vocabSize=10000,
        minDF=5.0
    )
    
    # IDF transformation
    idf = IDF(
        inputCol="raw_features",
        outputCol="features"
    )
    
    # Create pipeline
    pipeline = Pipeline(
        stages=[tokenizer, stopwords_remover, count_vectorizer, idf]
    )
    
    return pipeline

# COMMAND ----------

# MAGIC %md
# MAGIC ## Model Training

# COMMAND ----------

def train_sentiment_model(train_df, test_df):
    """
    Train sentiment classification model using MLflow.
    """
    
    with mlflow.start_run(run_name="sentiment_classification_v1") as run:
        # Create feature pipeline
        feature_pipeline = create_feature_pipeline()
        
        # Fit feature pipeline
        feature_model = feature_pipeline.fit(train_df)
        train_features = feature_model.transform(train_df)
        test_features = feature_model.transform(test_df)
        
        # Train classifier
        lr = LogisticRegression(
            featuresCol="features",
            labelCol="label",
            maxIter=100,
            regParam=0.01
        )
        
        # Train model
        model = lr.fit(train_features)
        
        # Make predictions
        train_predictions = model.transform(train_features)
        test_predictions = model.transform(test_features)
        
        # Evaluate
        evaluator = BinaryClassificationEvaluator(
            labelCol="label",
            rawPredictionCol="rawPrediction"
        )
        
        train_auc = evaluator.evaluate(train_predictions)
        test_auc = evaluator.evaluate(test_predictions)
        
        # Multiclass metrics
        multi_evaluator = MulticlassClassificationEvaluator(
            labelCol="label",
            predictionCol="prediction",
            metricName="accuracy"
        )
        
        train_accuracy = multi_evaluator.evaluate(train_predictions)
        test_accuracy = multi_evaluator.evaluate(test_predictions)
        
        # Log metrics
        mlflow.log_metric("train_auc", train_auc)
        mlflow.log_metric("test_auc", test_auc)
        mlflow.log_metric("train_accuracy", train_accuracy)
        mlflow.log_metric("test_accuracy", test_accuracy)
        
        # Log parameters
        mlflow.log_param("max_iter", 100)
        mlflow.log_param("reg_param", 0.01)
        mlflow.log_param("vocab_size", 10000)
        
        # Create full pipeline (features + model)
        full_pipeline = Pipeline(
            stages=feature_pipeline.getStages() + [model]
        )
        full_model = full_pipeline.fit(train_df)
        
        # Log model
        mlflow.spark.log_model(
            full_model,
            "sentiment_model",
            registered_model_name="customer_sentiment_classifier"
        )
        
        print(f"Training AUC: {train_auc:.4f}")
        print(f"Test AUC: {test_auc:.4f}")
        print(f"Training Accuracy: {train_accuracy:.4f}")
        print(f"Test Accuracy: {test_accuracy:.4f}")
        
        return full_model, feature_model, run.info.run_id

# COMMAND ----------

# MAGIC %md
# MAGIC ## Alternative: Transformer-Based Model

# COMMAND ----------

def train_transformer_model(train_df, test_df):
    """
    Alternative: Train using Hugging Face transformers for better accuracy.
    Requires Databricks ML Runtime with transformers.
    """
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
    from datasets import Dataset
    import torch
    
    # Convert Spark DataFrame to Pandas
    train_pd = train_df.select("text_cleaned", "label").toPandas()
    test_pd = test_df.select("text_cleaned", "label").toPandas()
    
    # Load pre-trained model
    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2
    )
    
    # Tokenize
    def tokenize_function(examples):
        return tokenizer(examples["text_cleaned"], truncation=True, padding=True)
    
    train_dataset = Dataset.from_pandas(train_pd)
    test_dataset = Dataset.from_pandas(test_pd)
    
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    test_dataset = test_dataset.map(tokenize_function, batched=True)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=100,
        evaluation_strategy="epoch"
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset
    )
    
    # Train
    trainer.train()
    
    # Log to MLflow
    with mlflow.start_run():
        mlflow.transformers.log_model(
            trainer.model,
            "sentiment_model_transformer",
            registered_model_name="customer_sentiment_transformer"
        )
    
    return trainer.model

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Training

# COMMAND ----------

# Prepare data
train_df, test_df = prepare_training_data()

# Train model
model, feature_model, run_id = train_sentiment_model(train_df, test_df)

print(f"Model training complete!")
print(f"MLflow Run ID: {run_id}")
print(f"Model registered as: customer_sentiment_classifier")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Model Evaluation & Validation

# COMMAND ----------

def evaluate_model_performance(model, test_df):
    """
    Comprehensive model evaluation.
    """
    predictions = model.transform(test_df)
    
    # Confusion matrix
    from pyspark.sql.functions import count
    
    confusion_matrix = (
        predictions
        .groupBy("label", "prediction")
        .agg(count("*").alias("count"))
        .orderBy("label", "prediction")
    )
    
    display(confusion_matrix)
    
    # Feature importance (for tree-based models)
    # For logistic regression, we can get coefficients
    if hasattr(model.stages[-1], 'coefficients'):
        feature_names = feature_model.stages[2].vocabulary  # CountVectorizer vocabulary
        coefficients = model.stages[-1].coefficients.toArray()
        
        importance_df = spark.createDataFrame(
            zip(feature_names[:len(coefficients)], coefficients),
            ["feature", "coefficient"]
        ).orderBy(col("coefficient").desc())
        
        print("Top 20 positive features:")
        display(importance_df.limit(20))
        
        print("Top 20 negative features:")
        display(importance_df.orderBy(col("coefficient").asc()).limit(20))
    
    return predictions

# Evaluate
test_predictions = evaluate_model_performance(model, test_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Model Registry & Promotion

# COMMAND ----------

from mlflow.tracking import MlflowClient

client = MlflowClient()

# Get latest model version
model_name = "customer_sentiment_classifier"
latest_version = client.get_latest_versions(model_name, stages=["None"])[0]

# Transition to Staging
client.transition_model_version_stage(
    name=model_name,
    version=latest_version.version,
    stage="Staging"
)

print(f"Model {model_name} version {latest_version.version} promoted to Staging")

# For production promotion (after validation):
# client.transition_model_version_stage(
#     name=model_name,
#     version=latest_version.version,
#     stage="Production"
# )
