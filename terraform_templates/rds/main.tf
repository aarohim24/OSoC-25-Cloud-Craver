resource "aws_db_subnet_group" "main" {
  name = "rds-subnet-group"
  subnet_ids = var.subnet_ids
  tags = {
    Name = "RDS Subnet Group"
  }
}

resource "aws_db_parameter_group" "main" {
  name = "rds-param-group"
  family = var.family
  description = "Custom RDS parameter group"
}

resource "aws_db_instance" "main" {
  identifier = "main-db"
  engine = var.engine
  engine_version = var.engine_version
  instance_class = var.db_instance_class
  username = var.db_username
  password = var.db_password
  allocated_storage = 20
  db_subnet_group_name = aws_db_subnet_group.main.name
  parameter_group_name = aws_db_parameter_group.main.name
  skip_final_snapshot = true
}
