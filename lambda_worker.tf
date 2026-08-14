resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${local.resource_name_prefix}-worker"
  retention_in_days = var.log_retention_in_days
  tags              = local.common_tags
}

resource "aws_lambda_function" "worker" {
  function_name = "${local.resource_name_prefix}-worker"
  description   = "Discord Gemini Worker (DynamoDB Streams CDC, Gemini API call, Discord response)"
  role          = aws_iam_role.worker.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  architectures = ["x86_64"]

  filename         = local.worker_zip_file
  source_code_hash = fileexists(local.worker_zip_file) ? filebase64sha256(local.worker_zip_file) : null

  memory_size = var.worker_memory_size
  timeout     = var.worker_timeout

  environment {
    variables = {
      GEMINI_API_KEY      = var.gemini_api_key
      GEMINI_MODEL        = var.gemini_model
      DISCORD_BOT_TOKEN   = var.discord_bot_token
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.sessions.name
      TTL_DAYS            = tostring(var.ttl_days)
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.worker,
    aws_iam_role_policy.worker,
  ]

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_name_prefix}-worker"
    }
  )
}

resource "aws_lambda_event_source_mapping" "dynamodb_stream" {
  event_source_arn               = aws_dynamodb_table.sessions.stream_arn
  function_name                  = aws_lambda_function.worker.arn
  starting_position              = "LATEST"
  batch_size                     = 1
  maximum_retry_attempts         = 3
  bisect_batch_on_function_error = true

  filter_criteria {
    filter {
      pattern = jsonencode({
        eventName = ["INSERT", "MODIFY"]
        dynamodb = {
          NewImage = {
            status = {
              S = ["PENDING"]
            }
          }
        }
      })
    }
  }
}
