# -----------------------------------------------------------------------------
# Automatic Download of Lambda ZIP assets from GitHub Releases
# -----------------------------------------------------------------------------

locals {
  github_release_base_url = "https://github.com/nizyu/terraform-aws-discord-gemini/releases/download/${var.release_tag}"
}

data "http" "ingress_zip" {
  count = var.ingress_zip_path == null ? 1 : 0
  url   = "${local.github_release_base_url}/ingress.zip"
}

data "http" "worker_zip" {
  count = var.worker_zip_path == null ? 1 : 0
  url   = "${local.github_release_base_url}/worker.zip"
}

resource "local_sensitive_file" "ingress_zip" {
  count          = var.ingress_zip_path == null ? 1 : 0
  content_base64 = data.http.ingress_zip[0].response_body_base64
  filename       = "${path.module}/.build/ingress-${var.release_tag}.zip"
}

resource "local_sensitive_file" "worker_zip" {
  count          = var.worker_zip_path == null ? 1 : 0
  content_base64 = data.http.worker_zip[0].response_body_base64
  filename       = "${path.module}/.build/worker-${var.release_tag}.zip"
}
