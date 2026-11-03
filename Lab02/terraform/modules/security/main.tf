resource "aws_default_security_group" "this" {
  #checkov:skip=CKV2_AWS_12:Default security group explicitly denies all ingress and egress traffic.
  vpc_id = var.vpc_id

  ingress = []
  egress  = []

  tags = {
    Name      = "${var.name}-default-sg"
    Project   = "NT548-Lab01"
    ManagedBy = "Terraform"
  }
}