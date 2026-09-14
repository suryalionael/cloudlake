# Main Terraform Configuration
# This file serves as the entry point for the CloudLake infrastructure

# All resource configurations are organized in separate files:
# - providers.tf: Terraform and AWS provider configuration
# - variables.tf: Input variables
# - outputs.tf: Output values
# - s3.tf: S3 buckets (data lake, Athena results)
# - iam.tf: IAM roles and policies
# - lambda.tf: Lambda functions for ingestion
# - glue.tf: Glue jobs, crawlers, and catalog
# - athena.tf: Athena workgroup
# - monitoring.tf: CloudWatch alarms

# Note: Backend configuration for state storage should be provided
# during terraform init or via backend.tfvars file
