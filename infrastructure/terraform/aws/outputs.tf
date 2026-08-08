output "provider" {
  value       = "aws"
  description = "Immutable provider identity for policy and workflow matching."
}

output "mode" {
  value       = var.mode
  description = "Installation mode selected for this independent AWS state."
}

output "vpc_id" {
  value       = module.network.vpc_id
  description = "Private-first VPC identifier."
}

output "private_subnet_ids" {
  value       = module.network.private_subnet_ids
  description = "Private subnets used by EKS control-plane ENIs and nodes."
}

output "cluster_name" {
  value       = module.eks_platform.cluster_name
  description = "Private EKS cluster name."
}

output "cluster_endpoint_private" {
  value       = true
  description = "The stack contract requires a private-only Kubernetes endpoint."
}

output "audit_bucket_name" {
  value       = module.security_logging.audit_bucket_name
  description = "Encrypted CloudTrail audit bucket."
}
