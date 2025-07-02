resource "azurerm_key_vault" "kv" {
  name                        = "\${var.prefix}-kv"
  location                    = var.location
  resource_group_name         = azurerm_resource_group.rg.name
  sku_name                    = "standard"
  tenant_id                   = var.tenant_id
  soft_delete_enabled         = true
  purge_protection_enabled    = true
  tags                        = var.tags
}

resource "azurerm_key_vault_secret" "secret" {
  name         = "db-password"
  value        = var.sql_password
  key_vault_id = azurerm_key_vault.kv.id
}