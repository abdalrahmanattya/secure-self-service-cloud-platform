variable "resource_group_id" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "monthly_budget_eur" {
  type = number
}

variable "alert_email" {
  type    = string
  default = ""
}
