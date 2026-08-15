terraform {
  required_version = ">= 1.11.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "discord_gemini" {
  source = "../.."

  name_prefix            = var.name_prefix
  discord_application_id = var.discord_application_id
  discord_public_key     = var.discord_public_key
  discord_bot_token      = var.discord_bot_token
  gemini_api_key         = var.gemini_api_key
  gemini_model           = var.gemini_model
  ttl_days               = var.ttl_days
}

output "interactions_endpoint_url" {
  description = "The Lambda Function URL to be set in Discord Developer Portal (Interactions Endpoint URL)"
  value       = module.discord_gemini.interactions_endpoint_url
}
