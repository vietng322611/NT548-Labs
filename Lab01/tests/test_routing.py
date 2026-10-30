from Lab01.tests.helpers import aws, check, cli, one, subnet


def main(args):
    """Check explicit subnet routes before or after NAT creation."""
    region, vpc_id = args.region, args.vpc_id
    tables = aws(region, "describe-route-tables", "--filters",
                 f"Name=vpc-id,Values={vpc_id}")["RouteTables"]
    for kind in ("public", "private"):
        subnet_id = subnet(vpc_id, region, kind)["SubnetId"]
        table = one(f"{kind} explicit route table association", [t for t in tables if any(
            a.get("SubnetId") == subnet_id and a.get("AssociationState", {}).get("State") == "associated"
            for a in t["Associations"])])
        routes = table["Routes"]
        check(f"{kind} local route", 1, sum(r.get("DestinationCidrBlock") == "10.0.0.0/16"
              and r.get("GatewayId") == "local" and r.get("State") == "active" for r in routes))
        defaults = [r for r in routes if r.get("DestinationCidrBlock") == "0.0.0.0/0"]
        if kind == "public":
            gateway = one("IGW", aws(region, "describe-internet-gateways", "--filters",
                          f"Name=attachment.vpc-id,Values={vpc_id}")["InternetGateways"])
            check("Public default route to IGW", 1, sum(r.get("GatewayId") == gateway["InternetGatewayId"]
                  and r.get("State") == "active" for r in defaults))
        elif args.stage == "before-nat":
            check("Private has no default route before NAT", 0, len(defaults))
        else:
            nat = one("Available NAT", aws(region, "describe-nat-gateways", "--filter",
                      f"Name=vpc-id,Values={vpc_id}", "Name=state,Values=available")["NatGateways"])
            check("Private default route to NAT", 1, sum(r.get("NatGatewayId") == nat["NatGatewayId"]
                  and r.get("State") == "active" for r in defaults))


if __name__ == "__main__":
    raise SystemExit(cli(main, stage=True))
