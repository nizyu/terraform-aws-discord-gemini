variable "aws_region" {
  description = "AWS Region to deploy resources"
  type        = string
  default     = "ap-northeast-1"
}

variable "name_prefix" {
  description = "Prefix for all resources"
  type        = string
  default     = "discord-gemini"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "discord_application_id" {
  description = "Discord Application ID"
  type        = string
}

variable "discord_public_key" {
  description = "Discord Public Key"
  type        = string
}

variable "discord_bot_token" {
  description = "Discord Bot Token"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Google Gemini API Key"
  type        = string
  sensitive   = true
}

variable "gemini_model" {
  description = "Gemini model name"
  type        = string
  default     = "gemini-3.7-flash"
}

variable "ttl_days" {
  description = "DynamoDB session TTL in days"
  type        = number
  default     = 7
}
