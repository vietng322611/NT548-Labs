output "vpc_id" {
  value = module.network.vpc_id
}

output "public_ec2_ip" {
  value = module.compute.public_ip
}

output "private_ec2_ip" {
  value = module.compute.private_ip
}