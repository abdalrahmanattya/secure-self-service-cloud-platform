resource "azurerm_consumption_budget_resource_group" "monthly" {
  name              = "${var.name_prefix}-monthly"
  resource_group_id = var.resource_group_id
  amount            = var.monthly_budget_eur
  time_grain        = "Monthly"

  time_period {
    start_date = "2026-01-01T00:00:00Z"
    end_date   = "2036-01-01T00:00:00Z"
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThan"
    threshold_type = "Forecasted"
    contact_emails = var.alert_email == "" ? [] : [var.alert_email]
  }
}
