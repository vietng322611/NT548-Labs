variable "ssh_cidr" {
  description = "Administrator public IPv4 address with /32"
  type        = string
}

variable "ssh_public_key" {
  type      = string
  sensitive = true
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}