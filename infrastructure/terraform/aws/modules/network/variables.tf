variable "name_prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "private_subnet_cidrs" {
  type = list(string)
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "nat_per_az" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
