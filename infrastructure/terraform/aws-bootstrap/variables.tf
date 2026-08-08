variable "region" {
  type    = string
  default = "eu-west-1"
}

variable "name_prefix" {
  type    = string
  default = "platform-bootstrap"
}

variable "state_bucket_name" {
  type        = string
  description = "Protected, organization-approved globally unique bucket name."
}

variable "github_repository" {
  type    = string
  default = "example-org/example-platform"

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "github_repository must be an exact owner/repository value."
  }
}

variable "github_plan_environment" {
  type    = string
  default = "platform-plan"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,31}$", var.github_plan_environment))
    error_message = "github_plan_environment must be a lowercase protected environment name."
  }
}

variable "github_apply_environment" {
  type    = string
  default = "platform-apply"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,31}$", var.github_apply_environment))
    error_message = "github_apply_environment must be a lowercase protected environment name."
  }
}

variable "github_destroy_environment" {
  type    = string
  default = "platform-destroy"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,31}$", var.github_destroy_environment))
    error_message = "github_destroy_environment must be a lowercase protected environment name."
  }
}
