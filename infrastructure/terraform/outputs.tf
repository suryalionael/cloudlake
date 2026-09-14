output "data_lake_bucket_name" {
  description = "Name of the S3 data lake bucket"
  value       = aws_s3_bucket.data_lake.id
}

output "data_lake_bucket_arn" {
  description = "ARN of the S3 data lake bucket"
  value       = aws_s3_bucket.data_lake.arn
}

output "athena_results_bucket_name" {
  description = "Name of the Athena results bucket"
  value       = aws_s3_bucket.athena_results.id
}

output "glue_database_name" {
  description = "Name of the Glue database"
  value       = aws_glue_catalog_database.cloudlake.name
}

output "lambda_function_names" {
  description = "Names of Lambda ingestion functions"
  value = {
    customers = aws_lambda_function.ingestion["customers"].function_name
    products  = aws_lambda_function.ingestion["products"].function_name
    stores    = aws_lambda_function.ingestion["stores"].function_name
    orders    = aws_lambda_function.ingestion["orders"].function_name
  }
}

output "glue_job_name" {
  description = "Name of the Glue processing job"
  value       = aws_glue_job.processing.name
}

output "account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS region"
  value       = data.aws_region.current.name
}
