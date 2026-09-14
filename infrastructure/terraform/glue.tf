# Glue Catalog Database
resource "aws_glue_catalog_database" "cloudlake" {
  name = var.project_name
}

# Glue Job for Data Processing
resource "aws_glue_job" "processing" {
  name     = "${var.project_name}-processing"
  role_arn = aws_iam_role.glue_processing.arn

  command {
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://${aws_s3_bucket.data_lake.id}/scripts/glue_processing.py"
  }

  default_arguments = {
    "--TempDir"                          = "s3://${aws_s3_bucket.data_lake.id}/temp/"
    "--job-language"                     = "python"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics"                   = "true"
    "--SOURCE_BUCKET"                    = aws_s3_bucket.data_lake.id
    "--TARGET_BUCKET"                    = aws_s3_bucket.data_lake.id
    "--DATABASE_NAME"                    = aws_glue_catalog_database.cloudlake.name
  }

  max_capacity = 1

  timeout = 60

  lifecycle {
    ignore_changes = [
      command[0].script_location,
    ]
  }
}

resource "aws_cloudwatch_log_group" "glue_processing" {
  name              = "/aws-glue/jobs/${aws_glue_job.processing.name}"
  retention_in_days = var.log_retention_days
}

# Glue Crawlers for Schema Discovery (optional, can be created later)
resource "aws_glue_crawler" "processed" {
  name          = "${var.project_name}-processed-crawler"
  role          = aws_iam_role.glue_processing.arn
  database_name = aws_glue_catalog_database.cloudlake.name

  s3_target {
    path = "s3://${aws_s3_bucket.data_lake.id}/processed/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })
}
