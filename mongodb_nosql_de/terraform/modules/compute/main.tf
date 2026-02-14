/**
 * Compute Module
 * 
 * Provisions EC2 instances or ECS tasks to run the data pipeline.
 * Includes IAM roles, instance profiles, and user data for configuration.
 */

# IAM Role for Pipeline Servers
resource "aws_iam_role" "pipeline" {
  name = "${var.project_name}-${var.environment}-pipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-pipeline-role"
  }
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy" "cloudwatch_logs" {
  name = "${var.project_name}-${var.environment}-cloudwatch-logs"
  role = aws_iam_role.pipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# IAM Policy for S3 Access (if needed for data sources)
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project_name}-${var.environment}-s3-access"
  role = aws_iam_role.pipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::*",
          "arn:aws:s3:::*/*"
        ]
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "pipeline" {
  name = "${var.project_name}-${var.environment}-pipeline-profile"
  role = aws_iam_role.pipeline.name
}

# Get latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# User data script for EC2 initialization
locals {
  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y python3 python3-pip git
    
    # Install MongoDB tools
    cat > /etc/yum.repos.d/mongodb-org-6.0.repo <<'REPO'
    [mongodb-org-6.0]
    name=MongoDB Repository
    baseurl=https://repo.mongodb.org/yum/amazon/2/mongodb-org/6.0/x86_64/
    gpgcheck=1
    enabled=1
    gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
    REPO
    
    yum install -y mongodb-org-tools
    
    # Create application directory
    mkdir -p /opt/data-pipeline
    chown ec2-user:ec2-user /opt/data-pipeline
    
    # Install Python dependencies (will be managed by Ansible)
    pip3 install --upgrade pip
    
    # Configure CloudWatch agent (optional)
    # yum install -y amazon-cloudwatch-agent
    
    # Set environment variables
    echo 'export MONGODB_URI="${var.mongodb_uri}"' >> /etc/environment
    echo 'export ENVIRONMENT="${var.environment}"' >> /etc/environment
    
    # Reboot to ensure all updates are applied
    reboot
  EOF
}

# Security Group (from VPC module)
data "aws_security_group" "pipeline" {
  id = var.security_group_id
}

# EC2 Instances for Pipeline
resource "aws_instance" "pipeline" {
  count                  = var.instance_count
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  vpc_security_group_ids = [data.aws_security_group.pipeline.id]
  subnet_id              = var.public_subnet_ids[count.index % length(var.public_subnet_ids)]
  iam_instance_profile   = aws_iam_instance_profile.pipeline.name

  user_data = base64encode(local.user_data)

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-pipeline-${count.index + 1}"
    Environment = var.environment
    Role        = "data-pipeline"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "pipeline" {
  name              = "/aws/ec2/${var.project_name}-${var.environment}-pipeline"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
