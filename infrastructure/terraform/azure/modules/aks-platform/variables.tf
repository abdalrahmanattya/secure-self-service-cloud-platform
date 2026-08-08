variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "tenant_id" {
  type = string
}

variable "kubernetes_version" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "log_workspace_id" {
  type = string
}

variable "node_vm_size" {
  type = string
}

variable "desired_nodes" {
  type = number
}

variable "tags" {
  type    = map(string)
  default = {}
}
