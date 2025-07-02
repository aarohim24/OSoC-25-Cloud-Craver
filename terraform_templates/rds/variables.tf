variable "subnet_ids" {}
variable "db_instance_class" {
  default = "db.t3.micro"
}
variable "db_username" {}
variable "db_password" {}
variable "engine" {
  default = "mysql"
}
variable "engine_version" {
  default = "8.0"
}
variable "family" {
  default = "mysql8.0"
}
