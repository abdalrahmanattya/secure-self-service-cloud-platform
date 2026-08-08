output "kms_key_arn" {
  value = aws_kms_key.audit.arn
}

output "audit_bucket_name" {
  value = aws_s3_bucket.audit.id
}

output "control_plane_log_group_name" {
  value = aws_cloudwatch_log_group.control_plane.name
}
