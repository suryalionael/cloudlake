variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "cloudlake"
}

variable "data_retention_days" {
  description = "Number of days to retain raw data in S3"
  type        = number
  default     = 90
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 14
}

variable "lambda_schedule_expression" {
  description = "Cron expression for Lambda ingestion schedule"
  type        = string
  default     = "cron(0 6 * * ? *)" # Daily at 6 AM UTC
}
