terraform {
  required_version = ">= 1.15.0, < 1.16.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 5.0.1"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "= 3.9.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}

provider "azuread" {
  tenant_id = var.tenant_id
}
