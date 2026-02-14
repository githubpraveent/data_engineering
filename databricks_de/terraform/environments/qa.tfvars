# QA environment configuration

environment             = "qa"
aws_region              = "us-east-1"
aws_zone_id             = "us-east-1a"
node_type_id            = "i3.xlarge"
num_workers             = 3

tags = {
  Environment = "qa"
  Project     = "retail-datalake"
  Team        = "data-engineering"
}

