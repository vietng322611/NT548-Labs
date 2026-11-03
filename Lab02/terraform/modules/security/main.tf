resource "aws_default_security_group" "this" {
  vpc_id = var.vpc_id

  ingress = []
  egress  = []

  tags = {
    Name      = "${var.name}-default-sg"
    Project   = var.name
    ManagedBy = "Terraform"
  }
}