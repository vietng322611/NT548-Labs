variable "ssh_cidr" {
  description = "Administrator public IPv4 address with /32"
  type        = string
}

variable "ssh_public_key" {
  type      = string
  sensitive = true
}