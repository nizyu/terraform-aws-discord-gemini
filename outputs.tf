output "interactions_endpoint_url" {
  description = "The Lambda Function URL to be set in Discord Developer Portal (Interactions Endpoint URL)"
  value       = aws_lambda_function_url.ingress.function_url
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table storing sessions and conversation context"
  value       = aws_dynamodb_table.sessions.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.sessions.arn
}

output "ingress_lambda_arn" {
  description = "ARN of the Ingress Lambda function"
  value       = aws_lambda_function.ingress.arn
}

output "worker_lambda_arn" {
  description = "ARN of the Worker Lambda function"
  value       = aws_lambda_function.worker.arn
}
