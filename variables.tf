variable "name_prefix" {
  description = "Prefix for all resources created by this module"
  type        = string
  default     = "discord-gemini"
}

variable "discord_application_id" {
  description = "Discord Application ID from Discord Developer Portal"
  type        = string
}

variable "discord_public_key" {
  description = "Discord Public Key for Ed25519 signature verification"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "discord_bot_token" {
  description = "Discord Bot Token for API access (threads and channel messages)"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "gemini_api_key" {
  description = "Google Gemini API Key from Google AI Studio"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "secrets_version" {
  description = "Version number for SSM parameters (increment when rotating secrets to update SSM values)"
  type        = number
  default     = 1
}

variable "gemini_model" {
  description = "Primary Gemini model to use for chat responses (e.g. gemini-3.7-flash)"
  type        = string
  default     = "gemini-3.7-flash"
}

variable "gemini_fallback_model" {
  description = "Secondary fallback Gemini model when primary model experiences high demand or errors (e.g. gemini-3.6-flash)"
  type        = string
  default     = "gemini-3.6-flash"
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
  default     = 120
}

variable "log_retention_in_days" {
  description = "Number of days to retain logs in CloudWatch Log Groups"
  type        = number
  default     = 14
}

variable "release_tag" {
  description = "Version tag of the release to download pre-built Lambda zip assets from GitHub Releases (e.g. v1.1.0)"
  type        = string
  default     = "v1.1.0"
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
