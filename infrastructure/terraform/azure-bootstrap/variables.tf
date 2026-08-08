variable "location" {
  type    = string
  default = "northeurope"
}

variable "resource_group_name" {
  type = string

  validation {
    condition     = can(regex("^[a-z0-9-]{3,63}$", var.resource_group_name))
    error_message = "resource_group_name must be a sanitized lowercase name."
  }
}

variable "storage_account_name" {
  type        = string
  description = "Protected, organization-approved globally unique storage account name."

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "storage_account_name must be 3-24 lowercase alphanumeric characters."
  }
}

variable "github_repository" {
  type    = string
  default = "example-org/example-platform"

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "github_repository must be an exact owner/repository value."
  }
}

variable "github_environment" {
  type    = string
  default = "platform"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,31}$", var.github_environment))
    error_message = "github_environment must be a lowercase protected environment name."
  }
}

variable "trusted_bootstrap_access" {
  type        = bool
  description = "Explicit temporary trusted operator access; false requires private endpoint inputs."
  default     = false
}

variable "private_endpoint_subnet_id" {
  type        = string
  description = "Protected subnet ID for the state storage private endpoint."
  default     = null
  nullable    = true
}

variable "private_dns_zone_ids" {
  type        = list(string)
  description = "Protected private DNS zone IDs for blob storage resolution."
  default     = []

  validation {
    condition     = var.trusted_bootstrap_access || (var.private_endpoint_subnet_id != null && length(var.private_dns_zone_ids) > 0)
    error_message = "Fail-closed bootstrap requires private_endpoint_subnet_id and private_dns_zone_ids unless trusted_bootstrap_access is explicitly true."
  }
}

variable "deployment_scope_id" {
  type        = string
  description = "Protected Azure resource ID at which the separate plan/apply/destroy identities are assigned."

  validation {
    condition     = can(regex("^/subscriptions/[0-9a-fA-F-]{36}(/resourceGroups/[A-Za-z0-9._()\\-]{1,90})?$", var.deployment_scope_id))
    error_message = "deployment_scope_id must be an operator-supplied subscription or resource-group resource ID."
  }
}
