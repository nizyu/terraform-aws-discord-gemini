terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    http = {
      source  = "hashicorp/http"
      version = ">= 3.0.0"
    }
    local = {
      source  = "hashicorp/local"
      version = ">= 2.0.0"
    }
  }
}

locals {
  resource_name_prefix = "${var.name_prefix}-${var.environment}"
  ingress_zip_file     = var.ingress_zip_path != null ? var.ingress_zip_path : (length(local_sensitive_file.ingress_zip) > 0 ? local_sensitive_file.ingress_zip[0].filename : "${path.module}/.build/ingress.zip")
  worker_zip_file      = var.worker_zip_path != null ? var.worker_zip_path : (length(local_sensitive_file.worker_zip) > 0 ? local_sensitive_file.worker_zip[0].filename : "${path.module}/.build/worker.zip")

  common_tags = merge(
    {
      Project     = var.name_prefix
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}
