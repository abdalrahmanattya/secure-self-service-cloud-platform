package aws

deny contains msg if {
  input.provider == "aws"
  input.resources.eks.endpoint_public_access == true
  msg := "EKS public API access must be disabled"
}

deny contains msg if {
  input.provider == "aws"
  input.resources.eks.node_subnet_visibility != "private"
  msg := "EKS nodes must be placed in private subnets"
}

deny contains msg if {
  input.provider == "aws"
  input.resources.eks.secrets_encryption != "kms"
  msg := "EKS Kubernetes secrets must use KMS encryption"
}

deny contains msg if {
  input.provider == "aws"
  input.resources.cloudtrail.enabled != true
  msg := "CloudTrail must be enabled"
}

deny contains msg if {
  input.provider == "aws"
  input.resources.cloudtrail.log_file_validation != true
  msg := "CloudTrail log file validation must be enabled"
}

deny contains msg if {
  input.provider == "aws"
  input.resources.s3.state_encryption != "kms"
  msg := "Terraform state must use KMS-backed S3 encryption"
}

deny contains msg if {
  input.provider == "aws"
  input.resources.s3.public_access_block != true
  msg := "Terraform and audit buckets must block public access"
}

deny contains msg if {
  input.provider == "aws"
  input.identity.federation.audience != "sts.amazonaws.com"
  msg := "AWS GitHub federation audience must be sts.amazonaws.com"
}

deny contains msg if {
  input.provider == "aws"
  not regex.match("^repo:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+:environment:[a-z0-9][a-z0-9-]{1,31}$", input.identity.federation.subject)
  msg := "AWS GitHub federation subject must be an exact repository Environment subject"
}

deny contains msg if {
  input.provider == "aws"
  input.identity.federation.lifecycle_roles.plan == input.identity.federation.lifecycle_roles.apply
  msg := "AWS plan and apply roles must be separate"
}

deny contains msg if {
  input.provider == "aws"
  input.identity.federation.lifecycle_roles.apply == input.identity.federation.lifecycle_roles.destroy
  msg := "AWS apply and destroy roles must be separate"
}

deny contains msg if {
  input.provider == "aws"
  some action in input.identity.federation.actions
  action == "iam:*"
  msg := "AWS federation policy must not grant iam:*"
}
