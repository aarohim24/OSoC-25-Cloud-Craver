terraform {
  backend "gcs" {
    bucket = var.gcs_bucket
    prefix = "env/${terraform.workspace}/terraform.tfstate"
  }
}