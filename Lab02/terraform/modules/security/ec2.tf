resource "aws_security_group" "public_ec2" {
  name        = "${var.name}-public-ec2-sg"
  description = "Allow SSH from administrator IP"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow SSH from administrator IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "${var.name}-public-ec2-sg"
    Project   = "NT548-Lab01"
    ManagedBy = "Terraform"
  }
}

resource "aws_security_group" "private_ec2" {
  name        = "${var.name}-private-ec2-sg"
  description = "Allow SSH from public EC2 security group"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow SSH from public EC2 security group"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.public_ec2.id]
  }

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "${var.name}-private-ec2-sg"
    Project   = "NT548-Lab01"
    ManagedBy = "Terraform"
  }
}