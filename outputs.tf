output "interactions_endpoint_url" {
  description = "The Lambda Function URL to be set in Discord Developer Portal (Interactions Endpoint URL)"
  value       = aws_lambda_function_url.ingress.function_url
}
