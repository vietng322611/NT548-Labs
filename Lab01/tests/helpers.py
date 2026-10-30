import argparse
import json
import subprocess
import sys


def check(name, expected, actual):
    if actual != expected:
        raise ValueError(f"{name}: expected={expected!r} actual={actual!r}")
    print(f"PASS {name}")


def one(name, items):
    check(f"{name} count", 1, len(items))
    return items[0]


def aws(region, *args):
    result = subprocess.run(
        ["aws", "ec2", *args, "--region", region, "--output", "json", "--no-cli-pager"],
        check=True, capture_output=True, text=True, timeout=120,
    )
    return json.loads(result.stdout)


def subnet(vpc_id, region, kind):
    cidr = "10.0.1.0/24" if kind == "public" else "10.0.2.0/24"
    return one(f"{kind} subnet", aws(region, "describe-subnets", "--filters",
               f"Name=vpc-id,Values={vpc_id}", f"Name=cidr-block,Values={cidr}")["Subnets"])


def instance(region, subnet_id, states, name):
    data = aws(region, "describe-instances", "--filters",
               f"Name=subnet-id,Values={subnet_id}", f"Name=instance-state-name,Values={states}")
    return one(name, [i for r in data["Reservations"] for i in r["Instances"]])


def cli(main, *, stage=False, security=False, ssh=False):
    parser = argparse.ArgumentParser(description=main.__doc__)
    if ssh:
        for name in ("public_ip", "private_ip", "nat_ip", "private_key"):
            parser.add_argument(name)
    else:
        parser.add_argument("vpc_id")
        if security:
            parser.add_argument("ssh_cidr", metavar="administrator-ip/32")
        parser.add_argument("region", nargs="?", default="us-east-1")
        if stage:
            parser.add_argument("stage", nargs="?", default="after-nat",
                                choices=("before-nat", "after-nat"))
    args = parser.parse_args()
    try:
        main(args)
    except (ValueError, KeyError, IndexError, TypeError, OSError, subprocess.SubprocessError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"FAIL {detail or exc}", file=sys.stderr)
        return 1
    return 0
