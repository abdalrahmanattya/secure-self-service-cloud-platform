output "role_arns" {
  value = { for lifecycle, role in aws_iam_role.github : lifecycle => role.arn }
}

output "subjects" {
  value = local.subjects
}
