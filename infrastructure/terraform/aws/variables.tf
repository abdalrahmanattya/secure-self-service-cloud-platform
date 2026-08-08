variable "region" {
  type        = string
  description = "AWS region supplied by the protected installation configuration."
  default     = "eu-west-1"
}

variable "name_prefix" {
  type        = string
  description = "Lowercase, sanitized resource prefix."
  default     = "platform-simulation"
}

variable "mode" {
  type        = string
  description = "Installation mode."
  default     = "simulation"

  validation {
    condition     = contains(["simulation", "sandbox", "enterprise"], var.mode)
    error_message = "mode must be simulation, sandbox, or enterprise."
  }
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR for the private-first VPC design."
  default     = "10.40.0.0/16"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "One private subnet CIDR per availability zone."
  default     = ["10.40.1.0/24", "10.40.2.0/24"]

  validation {
    condition     = length(var.private_subnet_cidrs) >= 2 && length(var.private_subnet_cidrs) <= 6 && alltrue([for cidr in var.private_subnet_cidrs : can(cidrhost(cidr, 0))])
    error_message = "private_subnet_cidrs must contain 2-6 valid CIDRs."
  }
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "Public egress subnets containing only controlled NAT gateways."
  default     = ["10.40.101.0/24", "10.40.102.0/24"]

  validation {
    condition     = length(var.public_subnet_cidrs) >= 2 && length(var.public_subnet_cidrs) <= 6 && alltrue([for cidr in var.public_subnet_cidrs : can(cidrhost(cidr, 0))])
    error_message = "public_subnet_cidrs must contain 2-6 valid CIDRs."
  }
}

variable "kubernetes_version" {
  type        = string
  description = "Approved EKS version supplied by the platform release process."
  default     = "1.36"
}

variable "node_instance_types" {
  type        = list(string)
  description = "Approved worker node instance types."
  default     = ["t3.medium"]
}

variable "desired_nodes" {
  type        = number
  description = "Desired worker node count."
  default     = 2
}

variable "monthly_budget_usd" {
  type        = number
  description = "Monthly budget guardrail in USD."
  default     = 150

  validation {
    condition     = var.monthly_budget_usd > 0 && var.monthly_budget_usd <= 1000000
    error_message = "monthly_budget_usd must be greater than zero and no more than 1,000,000."
  }
}

variable "budget_alert_email" {
  type        = string
  description = "Optional protected notification address; omit in simulation."
  default     = ""
}
