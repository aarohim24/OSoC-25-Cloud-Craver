resource "azurerm_sql_server" "primary" {
  name                         = "\${var.prefix}-sql"
  resource_group_name          = azurerm_resource_group.rg.name
  location                     = var.location
  version                      = "12.0"
  administrator_login          = var.sql_admin
  administrator_login_password = var.sql_password
  tags                         = var.tags
}

resource "azurerm_sql_database" "db" {
  name                = "\${var.prefix}-db"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  server_name         = azurerm_sql_server.primary.name
  sku_name            = "Basic"
  tags                = var.tags
}