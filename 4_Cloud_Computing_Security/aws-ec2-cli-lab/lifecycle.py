"""Explicit EC2 lifecycle plans; no AWS calls unless --execute is supplied."""
import argparse
import json
import ipaddress
import re
import subprocess
from pathlib import Path

TAG = "portfolio-ec2-cli"

def validate(config):
    patterns = {"region": r"[a-z]{2}(?:-[a-z]+)+-\d", "account": r"\d{12}", "ami": r"ami-[a-f0-9]{8,17}", "subnet": r"subnet-[a-f0-9]{8,17}", "security_group": r"sg-[a-f0-9]{8,17}", "key_name": r"[\w.-]{1,128}", "run_id": r"[a-zA-Z0-9-]{1,48}"}
    for key, pattern in patterns.items():
        if not re.fullmatch(pattern, str(config.get(key, ""))): raise ValueError("Invalid " + key)
    if config.get("instance_type", "t3.micro") not in {"t3.micro", "t3.small", "t2.micro"}: raise ValueError("Unsupported lab instance type")
    network = ipaddress.ip_network(config.get("admin_cidr", ""), strict=True)
    if network.version != 4 or network.prefixlen != 32: raise ValueError("admin_cidr must be one approved IPv4 /32")
    return config

def network_guard(group, c):
    permissions = group.get("IpPermissions", [])
    if not permissions: raise ValueError("No SSH ingress rule found")
    for rule in permissions:
        if rule.get("IpProtocol") != "tcp" or rule.get("FromPort") != 22 or rule.get("ToPort") != 22: raise ValueError("Lab group must allow only TCP/22 ingress")
        if rule.get("Ipv6Ranges") or rule.get("UserIdGroupPairs") or rule.get("PrefixListIds"): raise ValueError("Unexpected ingress source")
        ranges = rule.get("IpRanges", [])
        if not ranges or any(x["CidrIp"] != c["admin_cidr"] for x in ranges): raise ValueError("SSH source does not match admin_cidr")

def launch_args(c):
    validate(c)
    tags = [{"Key": "Project", "Value": TAG}, {"Key": "RunId", "Value": c["run_id"]}]
    return ["ec2", "run-instances", "--image-id", c["ami"], "--instance-type", c.get("instance_type", "t3.micro"), "--count", "1", "--subnet-id", c["subnet"], "--security-group-ids", c["security_group"], "--key-name", c["key_name"], "--metadata-options", "HttpTokens=required,HttpEndpoint=enabled", "--block-device-mappings", json.dumps([{"DeviceName": "/dev/xvda", "Ebs": {"Encrypted": True, "DeleteOnTermination": True, "VolumeType": "gp3", "VolumeSize": 8}}]), "--tag-specifications", json.dumps([{"ResourceType": kind, "Tags": tags} for kind in ["instance", "volume"]]), "--client-token", "portfolio-" + c["run_id"]]

def alarm_args(c, instance):
    return ["cloudwatch", "put-metric-alarm", "--alarm-name", "portfolio-" + c["run_id"], "--namespace", "AWS/EC2", "--metric-name", "CPUUtilization", "--dimensions", "Name=InstanceId,Value=" + instance, "--statistic", "Average", "--period", "300", "--evaluation-periods", "2", "--threshold", "80", "--comparison-operator", "GreaterThanOrEqualToThreshold", "--treat-missing-data", "missing"]

def owned(instance, c):
    tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
    return tags.get("Project") == TAG and tags.get("RunId") == c["run_id"]

def cli(args, c):
    result = subprocess.run(["aws", *args, "--region", c["region"], "--output", "json", "--no-cli-pager"], capture_output=True, text=True, timeout=120)
    if result.returncode: raise RuntimeError("AWS command failed: " + " ".join(args[:2]))
    return json.loads(result.stdout or "{}")

def execute(action, c, state_path, run=cli):
    if run(["sts", "get-caller-identity"], c)["Account"] != c["account"]: raise ValueError("Account mismatch")
    if action == "create":
        if state_path.exists(): raise ValueError("State already exists; reconcile it before another create")
        group = run(["ec2", "describe-security-groups", "--group-ids", c["security_group"]], c)["SecurityGroups"][0]
        network_guard(group, c)
        image = run(["ec2", "describe-images", "--image-ids", c["ami"]], c)["Images"][0]
        if image.get("Architecture") != "x86_64" or image.get("RootDeviceName") != "/dev/xvda" or image.get("RootDeviceType") != "ebs": raise ValueError("Use an x86_64 EBS-backed Amazon Linux image with /dev/xvda root")
        response = run(launch_args(c), c)
        instance = response["Instances"][0]["InstanceId"]
        # Persist before waiter/alarm: recover even if later calls fail.
        state_path.write_text(json.dumps({"instance_id": instance, "run_id": c["run_id"], "account": c["account"], "region": c["region"]}, indent=2))
        run(["ec2", "wait", "instance-running", "--instance-ids", instance], c)
        run(alarm_args(c, instance), c)
        return {"instance_id": instance, "state": "running", "alarm": "configured", "notification_actions": "none"}
    state = json.loads(state_path.read_text())
    if any(state[k] != c[k] for k in ["run_id", "account", "region"]): raise ValueError("State/config mismatch")
    instance = state["instance_id"]
    if not re.fullmatch(r"i-[a-f0-9]{8,17}", instance): raise ValueError("Invalid instance ID")
    response = run(["ec2", "describe-instances", "--instance-ids", instance], c)
    item = response["Reservations"][0]["Instances"][0]
    if not owned(item, c): raise ValueError("Ownership tags do not match")
    if action == "status": return {"instance_id": instance, "state": item["State"]["Name"]}
    run(["ec2", "terminate-instances", "--instance-ids", instance], c)
    run(["ec2", "wait", "instance-terminated", "--instance-ids", instance], c)
    run(["cloudwatch", "delete-alarms", "--alarm-names", "portfolio-" + c["run_id"]], c)
    return {"instance_id": instance, "state": "terminated", "alarm": "deleted"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["create", "status", "cleanup"])
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--state", type=Path, default=Path("state.local.json"))
    p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    try:
        c = validate(json.loads(a.config.read_text()))
        if a.execute: result = execute(a.action, c, a.state)
        else: result = {"mode": "offline-plan", "action": a.action, "launch_arguments": launch_args(c) if a.action == "create" else None, "cloud_calls": 0, "requires": "Explicit execution, matching account, approved network and owned state"}
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"status": "failed", "error": str(e)}))
        return 1

if __name__ == "__main__": raise SystemExit(main())
