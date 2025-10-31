resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "shortly-rds-subnet-group"
  subnet_ids = [aws_subnet.private.id]
  tags = { Name = "shortly-rds-subnet-group" }
}

resource "aws_db_instance" "postgres" {
  identifier              = "shortly-db"
  engine                  = "postgres"
  engine_version          = "15"
  instance_class          = var.instance_class
  allocated_storage       = 20
  storage_type            = "gp2"
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.rds_sg.id]
  skip_final_snapshot     = true
  publicly_accessible     = false
  tags = { Name = "shortly-rds" }
}
