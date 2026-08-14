variable "name_prefix" {
  description = "Prefix for all resources created by this module"
  type        = string
  default     = "discord-gemini"
}

variable "environment" {
  description = "Environment name (e.g. prod, dev, staging)"
  type        = string
  default     = "prod"
}

variable "discord_application_id" {
  description = "Discord Application ID from Discord Developer Portal"
  type        = string
}

variable "discord_public_key" {
  description = "Discord Public Key for Ed25519 signature verification"
  type        = string
}

variable "discord_bot_token" {
  description = "Discord Bot Token for API access (threads and channel messages)"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Google Gemini API Key from Google AI Studio"
  type        = string
  sensitive   = true
}

variable "gemini_model" {
  description = "Gemini model to use for chat responses"
  type        = string
  default     = "gemini-3.7-flash"
}

variable "ttl_days" {
  description = "Number of days before DynamoDB session records expire"
  type        = number
  default     = 7
}

variable "ingress_memory_size" {
  description = "Memory size for Ingress Lambda function (in MB)"
  type        = number
  default     = 256
}

variable "ingress_timeout" {
  description = "Timeout for Ingress Lambda function (in seconds, must be <= 3 for Discord)"
  type        = number
  default     = 5
}

variable "worker_memory_size" {
  description = "Memory size for Worker Lambda function (in MB)"
  type        = number
  default     = 256
}

variable "worker_timeout" {
  description = "Timeout for Worker Lambda function (in seconds)"
  type        = number
  default     = 60
}

variable "log_retention_in_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 14
}

variable "ingress_zip_path" {
  description = "Path to the pre-packaged Ingress Lambda zip file"
  type        = string
  default     = null
}

variable "worker_zip_path" {
  description = "Path to the pre-packaged Worker Lambda zip file"
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
