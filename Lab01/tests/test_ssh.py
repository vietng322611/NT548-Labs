from ipaddress import IPv4Address
from pathlib import Path
import subprocess
import tempfile

from Lab01.tests.helpers import check, cli


def main(args):
    """Check local-key SSH through public EC2 and private NAT egress."""
    for ip in (args.public_ip, args.private_ip, args.nat_ip):
        IPv4Address(ip)
    key = Path(args.private_key).expanduser().resolve()
    check("Private key file exists", True, key.is_file())
    # BatchMode cannot unlock keys: load the key into the local agent first.
    subprocess.run(["ssh-add", "-l"], check=True, capture_output=True, text=True, timeout=10)
    key_path = key.as_posix()
    check("Private key path usable in SSH config", False,
          any(c in key_path for c in ('\n', '\r', '%', '"')))
    # Local config makes host verification and identity apply to BOTH jump and target.
    config = (
        f'Host lab-public\n    HostName {args.public_ip}\n'
        f'Host lab-private\n    HostName {args.private_ip}\n    ProxyJump lab-public\n'
        'Host *\n    User ec2-user\n'
        f'    IdentityFile "{key_path}"\n'
        '    IdentitiesOnly yes\n    BatchMode yes\n    ForwardAgent no\n'
        '    StrictHostKeyChecking accept-new\n    ConnectTimeout 10\n'
    )
    with tempfile.TemporaryDirectory(prefix="lab01-ssh-") as directory:
        config_path = Path(directory) / "config"
        config_path.write_text(config, encoding="utf-8")
        for name, host, command in (
            ("SSH Public EC2", "lab-public", "hostname; ip -4 addr"),
            ("SSH Private EC2 via Public EC2", "lab-private", "hostname; ip -4 addr"),
            ("Private EC2 Internet access", "lab-private",
             "curl -4fsS --max-time 15 https://checkip.amazonaws.com"),
        ):
            result = subprocess.run(["ssh", "-F", str(config_path), host, command],
                                    check=True, capture_output=True, text=True, timeout=45)
            if result.stdout:
                print(result.stdout, end="")
            check(name, 0, result.returncode)
            if host == "lab-private" and command.startswith("curl "):
                check("Private EC2 NAT egress", args.nat_ip, result.stdout.strip())


if __name__ == "__main__":
    raise SystemExit(cli(main, ssh=True))
