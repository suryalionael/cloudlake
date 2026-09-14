# CloudWatch Alarms

# Lambda Ingestion Failure Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset(local.lambda_entities)

  alarm_name          = "${var.project_name}-lambda-${each.key}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Alert when ${each.key} Lambda ingestion fails"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.ingestion[each.key].function_name
  }
}

# Glue Job Failure Alarm
resource "aws_cloudwatch_metric_alarm" "glue_job_failure" {
  alarm_name          = "${var.project_name}-glue-job-failure"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "glue.driver.aggregate.numFailedTasks"
  namespace           = "Glue"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Alert when Glue processing job fails"
  treat_missing_data  = "notBreaching"

  dimensions = {
    JobName = aws_glue_job.processing.name
  }
}
