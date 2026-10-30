from Lab01.tests.helpers import aws, check, cli, one


def main(args):
    """Check available public NAT and its Elastic IP association."""
    region = args.region
    nat = one("Available NAT", aws(region, "describe-nat-gateways", "--filter",
              f"Name=vpc-id,Values={args.vpc_id}", "Name=state,Values=available")["NatGateways"])
    check("NAT connectivity", "public", nat["ConnectivityType"])
    subnet = one("NAT subnet", aws(region, "describe-subnets", "--subnet-ids", nat["SubnetId"])["Subnets"])
    check("NAT in public subnet", "10.0.1.0/24", subnet["CidrBlock"])
    address = one("NAT address", nat["NatGatewayAddresses"])
    eip = one("EIP", aws(region, "describe-addresses", "--allocation-ids", address["AllocationId"])["Addresses"])
    check("NAT public IP matches EIP", address["PublicIp"], eip["PublicIp"])
    check("EIP associated to NAT interface", address["NetworkInterfaceId"], eip["NetworkInterfaceId"])


if __name__ == "__main__":
    raise SystemExit(cli(main))
