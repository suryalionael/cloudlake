# Lambda Functions for Data Ingestion
locals {
  lambda_entities = ["customers", "products", "stores", "orders"]
}

resource "aws_lambda_function" "ingestion" {
  for_each = toset(local.lambda_entities)

  filename      = "${path.module}/lambda_deployment.zip"
  function_name = "${var.project_name}-ingestion-${each.key}"
  role          = aws_iam_role.lambda_ingestion.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  timeout       = 300
  memory_size   = 512
  
  source_code_hash = filebase64sha256("${path.module}/lambda_deployment.zip")

  environment {
    variables = {
      ENTITY           = each.key
      S3_BUCKET        = aws_s3_bucket.data_lake.id
      S3_PREFIX        = "raw/${each.key}"
      PARAMETER_PREFIX = "/${var.project_name}/api"
    }
  }
}

resource "aws_cloudwatch_log_group" "lambda_ingestion" {
  for_each = toset(local.lambda_entities)

  name              = "/aws/lambda/${aws_lambda_function.ingestion[each.key].function_name}"
  retention_in_days = var.log_retention_days
}

# EventBridge Rules for Scheduled Ingestion
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  for_each = toset(local.lambda_entities)

  name                = "${var.project_name}-ingestion-${each.key}-schedule"
  description         = "Schedule for ${each.key} ingestion"
  schedule_expression = var.lambda_schedule_expression
}

resource "aws_cloudwatch_event_target" "lambda_schedule" {
  for_each = toset(local.lambda_entities)

  rule      = aws_cloudwatch_event_rule.lambda_schedule[each.key].name
  target_id = "lambda"
  arn       = aws_lambda_function.ingestion[each.key].arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  for_each = toset(local.lambda_entities)

  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion[each.key].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule[each.key].arn
}

# Lambda deployment package is pre-built in src/lambda/
# and copied to terraform directory as lambda_deployment.zip
