terraform {
  backend "s3" {
    bucket         = var.s3_bucket
    key            = "env/${terraform.workspace}/terraform.tfstate"
    region         = var.aws_region
    encrypt        = true
    dynamodb_table = var.lock_table
  }
}