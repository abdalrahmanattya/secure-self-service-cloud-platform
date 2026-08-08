resource "aws_kms_key" "state" {
  description             = "Terraform state encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = { managed-by = "operator-run-bootstrap" }
}

resource "aws_kms_alias" "state" {
  name          = "alias/${var.name_prefix}-state"
  target_key_id = aws_kms_key.state.key_id
}

resource "aws_s3_bucket" "state" {
  bucket        = var.state_bucket_name
  force_destroy = false
  tags          = { managed-by = "operator-run-bootstrap" }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.state.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

module "github_oidc" {
  source = "../github-oidc"

  name_prefix                = var.name_prefix
  github_repository          = var.github_repository
  github_plan_environment    = var.github_plan_environment
  github_apply_environment   = var.github_apply_environment
  github_destroy_environment = var.github_destroy_environment
  state_bucket_arn           = aws_s3_bucket.state.arn
  state_kms_key_arn          = aws_kms_key.state.arn
}
