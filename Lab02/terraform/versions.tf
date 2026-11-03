terraform {
  required_version = "~> 1.16.0"

  backend "s3" {
    bucket       = "nt548-lab02"
    key          = "terraform.tfstate"
    region       = "ap-southeast-1"
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.70.0"
    }
  }
}