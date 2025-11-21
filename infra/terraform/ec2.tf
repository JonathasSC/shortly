resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  key_name = var.key_name
  
  tags = {
    Name = "shortly-ec2"
  }

  user_data = <<-EOF
              #!/bin/bash
              apt update -y
              apt install docker.io -y
              systemctl enable docker
              systemctl start docker
              EOF
}

resource "aws_eip" "app_ip" {
  instance = aws_instance.app.id
  tags = { Name = "shortly-eip" }
}
