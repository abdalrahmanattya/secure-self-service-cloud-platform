variable "cluster_name" {
  type = string
}

variable "kubernetes_version" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "kms_key_arn" {
  type = string
}

variable "node_instance_types" {
  type = list(string)
}

variable "desired_nodes" {
  type = number
}

variable "tags" {
  type    = map(string)
  default = {}
}
