variable "aws_region" {
  description = "Região da AWS"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "Tipo da instância EC2"
  type        = string
  default     = "t3.micro"
}

variable "db_username" {
  description = "Usuário do banco de dados"
  type        = string
}

variable "db_password" {
  description = "Senha do banco de dados"
  type        = string
  sensitive   = true
}

variable "key_name" {
  description = "Nome do par de chaves SSH"
  type        = string
}

variable "instance_class" {
  description = "Classe da instância"
  type = string
  default = "db.t3.micro"
}

variable "vpc_cidr" {
  description = "Bloco CIDR da VPC principal"
  type        = string
  default     = "10.0.0.0/16"
}

variable "vpc_name" {
  description = "Nome da VPC"
  type        = string
  default     = "shortly-vpc"
}

variable "igw_name" {
  description = "Nome do Internet Gateway"
  type        = string
  default     = "shortly-igw"
}

variable "public_subnet_cidr" {
  description = "Bloco CIDR da Subnet pública"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "Bloco CIDR da Subnet privada"
  type        = string
  default     = "10.0.2.0/24"
}

variable "public_subnet_name" {
  description = "Nome da Subnet pública"
  type        = string
  default     = "shortly-public"
}

variable "private_subnet_name" {
  description = "Nome da Subnet privada"
  type        = string
  default     = "shortly-private"
}

variable "public_rt_name" {
  description = "Nome da Tabela de Rota pública"
  type        = string
  default     = "shortly-public-rt"
}

variable "availability_zone" {
  description = "Zona de disponibilidade da VPC"
  type        = string
  default     = "us-east-1a"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}
