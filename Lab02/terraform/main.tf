module "network" {
  source = "./modules/network"

  name                = var.project_name
  vpc_cidr            = "10.0.0.0/16"
  public_subnet_cidr  = "10.0.1.0/24"
  private_subnet_cidr = "10.0.2.0/24"
  availability_zone   = "ap-southeast-1a"
}

module "security" {
  source = "./modules/security"

  name     = var.project_name
  vpc_id   = module.network.vpc_id
  ssh_cidr = var.ssh_cidr
}

module "routing" {
  source = "./modules/routing"

  name              = var.project_name
  vpc_id            = module.network.vpc_id
  public_subnet_id  = module.network.public_subnet_id
  private_subnet_id = module.network.private_subnet_id
  igw_id            = module.network.igw_id
}

module "compute" {
  source = "./modules/compute"

  name              = var.project_name
  public_subnet_id  = module.network.public_subnet_id
  private_subnet_id = module.network.private_subnet_id
  public_ec2_sg_id  = module.security.public_ec2_sg_id
  private_ec2_sg_id = module.security.private_ec2_sg_id
  ssh_public_key    = var.ssh_public_key

  depends_on = [module.routing]
}