variable "location" {
  type        = string
  description = "Azure region supplied by protected installation configuration."
  default     = "northeurope"
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

variable "tenant_id" {
  type        = string
  description = "Protected tenant ID supplied at runtime; never put a real value in public examples."
  sensitive   = true

  validation {
    condition     = can(regex("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", var.tenant_id)) && (var.mode == "simulation" || var.tenant_id != "00000000-0000-0000-0000-000000000000")
    error_message = "tenant_id must be a protected UUID; non-simulation modes cannot use the placeholder value."
  }
}

variable "subscription_id" {
  type        = string
  description = "Protected subscription ID supplied at runtime; never put a real value in public examples."
  sensitive   = true

  validation {
    condition     = can(regex("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", var.subscription_id)) && (var.mode == "simulation" || var.subscription_id != "00000000-0000-0000-0000-000000000000")
    error_message = "subscription_id must be a protected UUID; non-simulation modes cannot use the placeholder value."
  }
}

variable "vnet_address_space" {
  type    = list(string)
  default = ["10.50.0.0/16"]

  validation {
    condition     = length(var.vnet_address_space) > 0 && alltrue([for cidr in var.vnet_address_space : can(cidrhost(cidr, 0))])
    error_message = "vnet_address_space must contain valid CIDRs."
  }
}

variable "private_subnet_prefixes" {
  type    = list(string)
  default = ["10.50.1.0/24", "10.50.2.0/24"]

  validation {
    condition     = length(var.private_subnet_prefixes) >= 2 && length(var.private_subnet_prefixes) <= 6 && alltrue([for cidr in var.private_subnet_prefixes : can(cidrhost(cidr, 0))])
    error_message = "private_subnet_prefixes must contain 2-6 valid CIDRs."
  }
}

variable "kubernetes_version" {
  type        = string
  description = "Approved AKS version supplied by the platform release process."
  default     = "1.36"
}

variable "node_vm_size" {
  type    = string
  default = "Standard_D2s_v5"
}

variable "desired_nodes" {
  type    = number
  default = 2
}

variable "monthly_budget_eur" {
  type    = number
  default = 150

  validation {
    condition     = var.monthly_budget_eur > 0 && var.monthly_budget_eur <= 1000000
    error_message = "monthly_budget_eur must be greater than zero and no more than 1,000,000."
  }
}

variable "budget_alert_email" {
  type    = string
  default = ""
}
