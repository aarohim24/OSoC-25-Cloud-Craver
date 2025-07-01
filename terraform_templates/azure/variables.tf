variable "resource_group" {}
variable "location" {
  default = "East US"
}
variable "prefix" {
  default = "ccdev"
}
variable "tags" {
  type = map(string)
  default = {
    Environment = "Dev"
    Owner       = "CloudCraver"
  }
}
variable "admin_username" {}
variable "admin_password" {}
variable "sql_admin" {}
variable "sql_password" {}
variable "tenant_id" {}