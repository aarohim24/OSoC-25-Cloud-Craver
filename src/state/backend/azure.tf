terraform {
  backend "azurerm" {
    storage_account_name = var.azure_storage_account
    container_name       = var.azure_container
    key                  = "env/${terraform.workspace}/terraform.tfstate"
  }
}