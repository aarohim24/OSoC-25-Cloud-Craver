resource "azurerm_storage_account" "storage" {
  name                     = "\${var.prefix}stg"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = var.tags
}

resource "azurerm_storage_container" "container" {
  name                  = "app-container"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}