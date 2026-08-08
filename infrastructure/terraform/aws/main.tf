locals {
  common_tags = {
    managed-by   = "terraform"
    platform     = "secure-self-service-cloud-platform"
    installation = var.mode
  }
}

module "network" {
  source = "./modules/network"

  name_prefix          = var.name_prefix
  region               = var.region
  vpc_cidr             = var.vpc_cidr
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  nat_per_az           = var.mode == "enterprise"
  tags                 = local.common_tags
}

module "security_logging" {
  source = "./modules/security-logging"

  name_prefix = var.name_prefix
  tags        = local.common_tags
}

module "eks_platform" {
  source = "./modules/eks-platform"

  cluster_name        = "${var.name_prefix}-eks"
  kubernetes_version  = var.kubernetes_version
  private_subnet_ids  = module.network.private_subnet_ids
  kms_key_arn         = module.security_logging.kms_key_arn
  node_instance_types = var.node_instance_types
  desired_nodes       = var.desired_nodes
  tags                = local.common_tags
}

module "budget_guardrails" {
  source = "./modules/budget-guardrails"

  name_prefix        = var.name_prefix
  monthly_budget_usd = var.monthly_budget_usd
  alert_email        = var.budget_alert_email
  tags               = local.common_tags
}
