variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "storage_account_name" {
  type = string
}

variable "trusted_bootstrap_access" {
  type = bool
}

variable "private_endpoint_subnet_id" {
  type     = string
  default  = null
  nullable = true
}

variable "private_dns_zone_ids" {
  type    = list(string)
  default = []
}

variable "deployment_scope_id" {
  type = string
}

variable "github_repository" {
  type = string
}

variable "github_environment" {
  type = string
}
