from ipaddress import IPv4Network

from Lab01.tests.helpers import aws, check, cli, instance, one, subnet


def main(args):
    """Check administrator /32 SSH and private SSH only from public SG."""
    network = IPv4Network(args.ssh_cidr)
    check("Administrator CIDR format", True,
          network.prefixlen == 32 and str(network) == args.ssh_cidr)
    region, public_sg = args.region, None
    for kind in ("public", "private"):
        subnet_id = subnet(args.vpc_id, region, kind)["SubnetId"]
        item = instance(region, subnet_id, "running", f"{kind} running instance")
        group_id = one(f"{kind} attached SG", item["SecurityGroups"])["GroupId"]
        group = one(f"{kind} SG", aws(region, "describe-security-groups", "--group-ids", group_id)["SecurityGroups"])
        check(f"{kind} SG belongs to VPC", args.vpc_id, group["VpcId"])
        check(f"{kind} SG is custom", True, group["GroupName"] != "default")
        rule = one(f"{kind} inbound rule", group["IpPermissions"])
        check(f"{kind} inbound only TCP 22", True,
              rule["IpProtocol"] == "tcp" and rule.get("FromPort") == 22
              and rule.get("ToPort") == 22 and not rule.get("Ipv6Ranges")
              and not rule.get("PrefixListIds"))
        if kind == "public":
            public_sg = group_id
            check("Public SSH only administrator /32", True,
                  [r["CidrIp"] for r in rule.get("IpRanges", [])] == [args.ssh_cidr]
                  and not rule.get("UserIdGroupPairs"))
        else:
            check("Private SG differs from public SG", True, group_id != public_sg)
            check("Private SSH only public SG", True,
                  [r["GroupId"] for r in rule.get("UserIdGroupPairs", [])] == [public_sg]
                  and not rule.get("IpRanges"))
        check(f"{kind} outbound allows all IPv4", True, any(
            r["IpProtocol"] == "-1" and any(ip["CidrIp"] == "0.0.0.0/0" for ip in r.get("IpRanges", []))
            for r in group["IpPermissionsEgress"]))


if __name__ == "__main__":
    raise SystemExit(cli(main, security=True))
