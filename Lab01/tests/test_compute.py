from Lab01.tests.helpers import aws, check, cli, instance, one, subnet


def main(args):
    """Check both EC2 instances, AMI, key pair, root volume and status checks."""
    region = args.region
    for kind in ("public", "private"):
        subnet_id = subnet(args.vpc_id, region, kind)["SubnetId"]
        item = instance(region, subnet_id, "pending,running,stopping,stopped", f"{kind} instance")
        check(f"{kind} instance state", "running", item["State"]["Name"])
        check(f"{kind} instance type", "t3.micro", item["InstanceType"])
        check(f"{kind} public IPv4 presence", kind == "public", bool(item.get("PublicIpAddress")))
        key = item.get("KeyName", "")
        check(f"{kind} key configured", True, bool(key))
        one(f"{kind} key pair", aws(region, "describe-key-pairs", "--key-names", key)["KeyPairs"])
        image = one(f"{kind} image", aws(region, "describe-images", "--image-ids", item["ImageId"])["Images"])
        check(f"{kind} Amazon Linux 2023", True, image.get("Name", "").startswith("al2023-ami-"))
        mapping = one(f"{kind} root mapping", [m for m in item["BlockDeviceMappings"]
                      if m["DeviceName"] == item["RootDeviceName"]])["Ebs"]
        check(f"{kind} root delete on termination", True, mapping["DeleteOnTermination"])
        volume = one(f"{kind} root volume", aws(region, "describe-volumes", "--volume-ids", mapping["VolumeId"])["Volumes"])
        check(f"{kind} root volume type", "gp3", volume["VolumeType"])
        check(f"{kind} root volume size GiB", 8, volume["Size"])
        check(f"{kind} root volume state", "in-use", volume["State"])
        status = one(f"{kind} instance status", aws(region, "describe-instance-status",
                     "--instance-ids", item["InstanceId"])["InstanceStatuses"])
        check(f"{kind} system status", "ok", status["SystemStatus"]["Status"])
        check(f"{kind} instance status", "ok", status["InstanceStatus"]["Status"])


if __name__ == "__main__":
    raise SystemExit(cli(main))
