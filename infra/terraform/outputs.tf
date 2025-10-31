output "ec2_public_ip" {
  value = aws_eip.app_ip.public_ip
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}
