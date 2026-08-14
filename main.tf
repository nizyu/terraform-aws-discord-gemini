locals {
  resource_name_prefix = "${var.name_prefix}-${var.environment}"
  default_ingress_zip  = "${path.module}/.build/ingress.zip"
  default_worker_zip   = "${path.module}/.build/worker.zip"
  ingress_zip_file     = var.ingress_zip_path != null ? var.ingress_zip_path : local.default_ingress_zip
  worker_zip_file      = var.worker_zip_path != null ? var.worker_zip_path : local.default_worker_zip

  common_tags = merge(
    {
      Project     = var.name_prefix
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}
