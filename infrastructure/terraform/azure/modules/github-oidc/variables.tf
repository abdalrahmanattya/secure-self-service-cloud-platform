variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "name_prefix" {
  type = string
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

variable "tags" {
  type    = map(string)
  default = {}
}
