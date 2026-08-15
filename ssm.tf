# -----------------------------------------------------------------------------
# AWS Systems Manager (SSM) Parameter Store (Secure Secrets Storage)
# Uses Write-Only (value_wo) attributes to avoid saving secrets in terraform.tfstate
# -----------------------------------------------------------------------------

resource "aws_ssm_parameter" "discord_public_key" {
  name             = "/${local.resource_name_prefix}/discord_public_key"
  description      = "Discord Public Key for interaction signature verification"
  type             = "SecureString"
  value_wo         = var.discord_public_key
  value_wo_version = var.secrets_version
  tags             = local.common_tags
}

resource "aws_ssm_parameter" "discord_bot_token" {
  name             = "/${local.resource_name_prefix}/discord_bot_token"
  description      = "Discord Bot Token for Discord REST API operations"
  type             = "SecureString"
  value_wo         = var.discord_bot_token
  value_wo_version = var.secrets_version
  tags             = local.common_tags
}

resource "aws_ssm_parameter" "gemini_api_key" {
  name             = "/${local.resource_name_prefix}/gemini_api_key"
  description      = "Google Gemini API Key from Google AI Studio"
  type             = "SecureString"
  value_wo         = var.gemini_api_key
  value_wo_version = var.secrets_version
  tags             = local.common_tags
}
