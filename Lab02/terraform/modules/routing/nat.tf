resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name      = "${var.name}-nat-eip"
    Project   = var.project_name
    ManagedBy = "Terraform"
  }
}

resource "aws_nat_gateway" "this" {
  allocation_id     = aws_eip.nat.id
  subnet_id         = var.public_subnet_id
  connectivity_type = "public"

  tags = {
    Name      = "${var.name}-nat"
    Project   = var.project_name
    ManagedBy = "Terraform"
  }

  depends_on = [aws_route.public_internet]
}

resource "aws_route" "private_internet" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this.id
}