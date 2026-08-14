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
  resource_name_prefix = var.name_prefix

  ingress_zip_file = var.ingress_zip_path != null ? var.ingress_zip_path : local_sensitive_file.ingress_zip[0].filename
  worker_zip_file  = var.worker_zip_path != null ? var.worker_zip_path : local_sensitive_file.worker_zip[0].filename

  ingress_source_hash = var.ingress_zip_path != null ? filebase64sha256(var.ingress_zip_path) : local_sensitive_file.ingress_zip[0].content_base64sha256
  worker_source_hash  = var.worker_zip_path != null ? filebase64sha256(var.worker_zip_path) : local_sensitive_file.worker_zip[0].content_base64sha256

  common_tags = merge(
    {
      Project   = var.name_prefix
      ManagedBy = "Terraform"
    },
    var.tags
  )
}
