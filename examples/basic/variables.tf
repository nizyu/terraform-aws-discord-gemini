variable "aws_region" {
  description = "AWS Region to deploy resources (leave null to use default AWS provider / CLI profile region)"
  type        = string
  default     = null
}

variable "name_prefix" {
  description = "Prefix for all resources"
  type        = string
  default     = "discord-gemini"
}

variable "discord_application_id" {
  description = "Discord Application ID"
  type        = string
}

variable "discord_public_key" {
  description = "Discord Public Key"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "discord_bot_token" {
  description = "Discord Bot Token"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "gemini_api_key" {
  description = "Google Gemini API Key"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "gemini_models" {
  description = "List of Gemini models in priority order with fallback"
  type        = list(string)
  default     = ["gemini-3.7-flash", "gemini-3.6-flash"]
}

variable "ttl_days" {
  description = "DynamoDB session TTL in days"
  type        = number
  default     = 7
}
