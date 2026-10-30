from Lab01.tests.helpers import aws, check, cli, one, subnet


def main(args):
    """Check VPC, subnets, attached IGW and default security group."""
    region, vpc_id = args.region, args.vpc_id
    vpc = one("VPC", aws(region, "describe-vpcs", "--vpc-ids", vpc_id)["Vpcs"])
    check("VPC state", "available", vpc["State"])
    check("VPC CIDR", "10.0.0.0/16", vpc["CidrBlock"])
    for attribute, field in (("enableDnsSupport", "EnableDnsSupport"),
                             ("enableDnsHostnames", "EnableDnsHostnames")):
        data = aws(region, "describe-vpc-attribute", "--vpc-id", vpc_id, "--attribute", attribute)
        check(field, True, data[field]["Value"])
    for kind in ("public", "private"):
        item = subnet(vpc_id, region, kind)
        check(f"{kind} subnet state", "available", item["State"])
        check(f"{kind} subnet AZ", "us-east-1a", item["AvailabilityZone"])
        check(f"{kind} subnet auto public IPv4", kind == "public", item["MapPublicIpOnLaunch"])
    gateways = aws(region, "describe-internet-gateways", "--filters",
                   f"Name=attachment.vpc-id,Values={vpc_id}")["InternetGateways"]
    check("IGW attached to VPC", 1, sum(any(a["VpcId"] == vpc_id and a["State"] == "available"
          for a in g["Attachments"]) for g in gateways))
    groups = aws(region, "describe-security-groups", "--filters",
                 f"Name=vpc-id,Values={vpc_id}", "Name=group-name,Values=default")["SecurityGroups"]
    check("Default security group exists", 1, len(groups))


if __name__ == "__main__":
    raise SystemExit(cli(main))
