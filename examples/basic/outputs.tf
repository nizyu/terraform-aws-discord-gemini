output "discord_interactions_endpoint_url" {
  description = "The Lambda Function URL to be set in Discord Developer Portal (Interactions Endpoint URL)"
  value       = module.discord_gemini.interactions_endpoint_url
}

output "dynamodb_table_name" {
  description = "DynamoDB Table Name"
  value       = module.discord_gemini.dynamodb_table_name
}
