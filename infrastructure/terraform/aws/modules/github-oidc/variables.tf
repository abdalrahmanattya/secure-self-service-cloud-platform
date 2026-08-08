variable "name_prefix" {
  type = string
}

variable "github_repository" {
  type = string
}

variable "github_plan_environment" {
  type = string
}

variable "github_apply_environment" {
  type = string
}

variable "github_destroy_environment" {
  type = string
}

variable "state_bucket_arn" {
  type = string
}

variable "state_kms_key_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
