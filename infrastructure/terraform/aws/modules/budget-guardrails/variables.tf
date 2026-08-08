variable "name_prefix" {
  type = string
}

variable "monthly_budget_usd" {
  type = number
}

variable "alert_email" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
