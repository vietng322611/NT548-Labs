import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import patch

from Lab01.tests.helpers import aws, check, cli, one


class TestHelper(unittest.TestCase):
    def test_helpers_offline(self):
        with patch("common.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, '{"Vpcs": []}', "")
            self.assertEqual(aws("us-east-1", "describe-vpcs"), {"Vpcs": []})
            self.assertEqual(run.call_args.args[0], ["aws", "ec2", "describe-vpcs",
                             "--region", "us-east-1", "--output", "json", "--no-cli-pager"])
            self.assertTrue(run.call_args.kwargs["check"])
            self.assertNotIn("shell", run.call_args.kwargs)
            run.return_value.stdout = "not JSON"
            with self.assertRaises(json.JSONDecodeError):
                aws("us-east-1", "describe-vpcs")
            run.side_effect = subprocess.CalledProcessError(1, ["aws"], stderr="denied")
            with self.assertRaises(subprocess.CalledProcessError):
                aws("us-east-1", "describe-vpcs")
            with patch("sys.argv", ["test", "vpc-offline"]), contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(cli(lambda args: aws(args.region, "describe-vpcs")), 1)
                self.assertIn("FAIL denied", error.getvalue())
        with contextlib.redirect_stdout(io.StringIO()) as output:
            check("equal", True, True)
            self.assertEqual(one("single", [42]), 42)
        self.assertIn("PASS equal", output.getvalue())
        with self.assertRaises(ValueError):
            check("different", 1, 2)
        with self.assertRaises(ValueError):
            one("missing", [])


if __name__ == "__main__":
    unittest.main()
