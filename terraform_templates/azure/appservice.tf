resource "azurerm_app_service_plan" "plan" {
  name                = "\${var.prefix}-plan"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "Linux"
  reserved            = true

  sku {
    tier = "Basic"
    size = "B1"
  }

  tags = var.tags
}

resource "azurerm_app_service" "app" {
  name                = "\${var.prefix}-app"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  app_service_plan_id = azurerm_app_service_plan.plan.id

  site_config {
    linux_fx_version = "NODE|18-lts"
  }

  tags = var.tags
}

resource "azurerm_app_service_slot" "staging" {
  name                = "staging"
  resource_group_name = azurerm_resource_group.rg.name
  app_service_name    = azurerm_app_service.app.name
  app_service_plan_id = azurerm_app_service_plan.plan.id
}