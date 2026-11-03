# checkov:skip=CKV2_AWS_11:VPC Flow Logs are omitted in this lab to avoid additional monitoring costs.
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name      = "${var.name}-vpc"
    Project   = "NT548-Lab01"
    ManagedBy = "Terraform"
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name      = "${var.name}-igw"
    Project   = "NT548-Lab01"
    ManagedBy = "Terraform"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = false

  tags = {
    Name      = "${var.name}-public-subnet"
    Project   = "NT548-Lab01"
    ManagedBy = "Terraform"
  }
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.private_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = false

  tags = {
    Name      = "${var.name}-private-subnet"
    Project   = "NT548-Lab01"
    ManagedBy = "Terraform"
  }
}