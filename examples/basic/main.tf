terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Auto-build zip files before deploying if not present
resource "null_resource" "build_lambdas" {
  triggers = {
    ingress_handler = filebase64sha256("${path.module}/../../src/ingress/handler.py")
    worker_handler  = filebase64sha256("${path.module}/../../src/worker/handler.py")
    gemini_client   = filebase64sha256("${path.module}/../../src/worker/gemini_client.py")
    discord_client  = filebase64sha256("${path.module}/../../src/worker/discord_client.py")
  }

  provisioner "local-exec" {
    command = "python3 ${path.module}/../../scripts/package.py"
  }
}

module "discord_gemini" {
  source = "../.."

  name_prefix            = var.name_prefix
  environment            = var.environment
  discord_application_id = var.discord_application_id
  discord_public_key     = var.discord_public_key
  discord_bot_token      = var.discord_bot_token
  gemini_api_key         = var.gemini_api_key
  gemini_model           = var.gemini_model
  ttl_days               = var.ttl_days

  depends_on = [
    null_resource.build_lambdas
  ]
}
