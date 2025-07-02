output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}
output "vm_name" {
  value = azurerm_windows_virtual_machine.vm.name
}
output "sql_db_name" {
  value = azurerm_sql_database.db.name
}