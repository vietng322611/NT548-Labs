data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-6.1-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "this" {
  key_name   = "${var.name}-key"
  public_key = var.ssh_public_key
}

resource "aws_instance" "public" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = "t3.micro"
  subnet_id                   = var.public_subnet_id
  vpc_security_group_ids      = [var.public_ec2_sg_id]
  key_name                    = aws_key_pair.this.key_name
  associate_public_ip_address = true

  root_block_device {
    volume_size           = 8
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name      = "${var.name}-public-ec2"
    Project   = "NT548-Lab01"
    ManagedBy = "Terraform"
  }
}

resource "aws_instance" "private" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = "t3.micro"
  subnet_id                   = var.private_subnet_id
  vpc_security_group_ids      = [var.private_ec2_sg_id]
  key_name                    = aws_key_pair.this.key_name
  associate_public_ip_address = false

  root_block_device {
    volume_size           = 8
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name      = "${var.name}-private-ec2"
    Project   = "NT548-Lab01"
    ManagedBy = "Terraform"
  }
}