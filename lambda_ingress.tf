resource "aws_cloudwatch_log_group" "ingress" {
  name              = "/aws/lambda/${local.resource_name_prefix}-ingress"
  retention_in_days = var.log_retention_in_days
  tags              = local.common_tags
}

resource "aws_lambda_function" "ingress" {
  function_name = "${local.resource_name_prefix}-ingress"
  description   = "Discord Interaction Ingress Handler (Signature verification and defer response)"
  role          = aws_iam_role.ingress.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  architectures = ["x86_64"]

  filename         = local.ingress_zip_file
  source_code_hash = fileexists(local.ingress_zip_file) ? filebase64sha256(local.ingress_zip_file) : null

  memory_size = var.ingress_memory_size
  timeout     = var.ingress_timeout

  environment {
    variables = {
      DISCORD_PUBLIC_KEY  = var.discord_public_key
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.sessions.name
      TTL_DAYS            = tostring(var.ttl_days)
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.ingress,
    aws_iam_role_policy.ingress,
    local_sensitive_file.ingress_zip,
  ]

  tags = merge(
    local.common_tags,
    {
      Name = "${local.resource_name_prefix}-ingress"
    }
  )
}

resource "aws_lambda_function_url" "ingress" {
  function_name      = aws_lambda_function.ingress.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST", "GET", "OPTIONS"]
    allow_headers     = ["*"]
    max_age           = 86400
  }
}
