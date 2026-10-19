import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import lifecycle as l

C = json.loads(Path("config.example.json").read_text())
I = "i-0123456789abcdef0"
GROUP = {"IpPermissions": [{"IpProtocol":"tcp", "FromPort":22, "ToPort":22, "IpRanges":[{"CidrIp":C["admin_cidr"]}]}]}
IMAGE = {"Architecture":"x86_64", "RootDeviceName":"/dev/xvda", "RootDeviceType":"ebs"}
class LifecycleTests(unittest.TestCase):
    def test_metadata_and_single_instance(self):
        args = l.launch_args(C)
        self.assertIn("HttpTokens=required,HttpEndpoint=enabled", args)
        self.assertEqual(args[args.index("--count")+1], "1")
    def test_volumes_encrypted_and_tagged(self):
        args = l.launch_args(C)
        self.assertTrue(json.loads(args[args.index("--block-device-mappings")+1])[0]["Ebs"]["Encrypted"])
        self.assertEqual(len(json.loads(args[args.index("--tag-specifications")+1])), 2)
    def test_invalid_config(self):
        for key in ["account", "ami", "subnet", "security_group", "run_id"]:
            with self.assertRaises(ValueError): l.validate({**C, key: "bad value"})
    def test_account_mismatch_blocks_launch(self):
        run = Mock(return_value={"Account": "999999999999"})
        with self.assertRaises(ValueError): l.execute("create", C, Path("unused"), run)
        self.assertEqual(run.call_count, 1)
    def test_state_saved_before_alarm_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)/"state.json"
            run = Mock(side_effect=[{"Account": C["account"]}, {"SecurityGroups":[GROUP]}, {"Images":[IMAGE]}, {"Instances": [{"InstanceId": I}]}, {}, RuntimeError("alarm failed")])
            with self.assertRaises(RuntimeError): l.execute("create", C, state, run)
            self.assertEqual(json.loads(state.read_text())["instance_id"], I)
    def test_existing_state_blocks_create(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)/"state.json"; state.write_text("{}")
            run = Mock(return_value={"Account": C["account"]})
            with self.assertRaises(ValueError): l.execute("create", C, state, run)
            self.assertEqual(run.call_count, 1)
    def fixture(self, temp):
        state = Path(temp)/"state.json"
        state.write_text(json.dumps({"instance_id": I, **{k:C[k] for k in ["account", "region", "run_id"]}}))
        return state
    def test_foreign_tags_block_termination(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Mock(side_effect=[{"Account": C["account"]}, {"Reservations": [{"Instances": [{"Tags": [], "State": {"Name": "running"}}]}]}])
            with self.assertRaises(ValueError): l.execute("cleanup", C, self.fixture(temp), run)
            self.assertEqual(run.call_count, 2)
    def test_cleanup_waits_then_deletes_alarm(self):
        with tempfile.TemporaryDirectory() as temp:
            tags = [{"Key":"Project", "Value":l.TAG},{"Key":"RunId", "Value":C["run_id"]}]
            run = Mock(side_effect=[{"Account": C["account"]}, {"Reservations": [{"Instances": [{"Tags": tags}]}]}, {}, {}, {}])
            self.assertEqual(l.execute("cleanup", C, self.fixture(temp), run)["state"], "terminated")
            self.assertEqual(run.call_args_list[-2].args[0][:3], ["ec2", "wait", "instance-terminated"])
    def test_alarm_has_no_unverified_email_claim(self):
        self.assertNotIn("--alarm-actions", l.alarm_args(C, I))
    def test_open_ssh_rejected(self):
        group = {"IpPermissions": [{"IpProtocol":"tcp", "FromPort":22,"ToPort":22,"IpRanges":[{"CidrIp":"0.0.0.0/0"}]}]}
        with self.assertRaises(ValueError): l.network_guard(group, C)
    def test_missing_ssh_rejected(self):
        with self.assertRaises(ValueError): l.network_guard({}, C)
    def test_wide_admin_range_rejected(self):
        with self.assertRaises(ValueError): l.validate({**C,"admin_cidr":"192.0.2.0/24"})
    def test_unexpected_ipv6_rejected(self):
        group = {"IpPermissions":[{**GROUP["IpPermissions"][0], "Ipv6Ranges":[{"CidrIpv6":"::/0"}]}]}
        with self.assertRaises(ValueError): l.network_guard(group, C)
    def test_expected_network_allowed(self): l.network_guard(GROUP,C)

if __name__ == "__main__": unittest.main()
