import tempfile
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import verify_openpgp as v

class OpenPGPTests(unittest.TestCase):
    def test_existing_home_refused(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError): v.exercise(Path(folder))
    def test_missing_executable_fails(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(v.shutil, "which", return_value=None), self.assertRaises(RuntimeError): v.exercise(Path(folder)/"new")
    def test_failed_key_generation_is_not_success(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(v.shutil, "which", return_value="gpg"), patch.object(v.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "failed")), self.assertRaises(RuntimeError): v.exercise(Path(folder)/"new")
    def fake_run(self, cmd, **kwargs):
        self.commands.append((cmd, kwargs))
        if "--with-colons" in cmd: return subprocess.CompletedProcess(cmd, 0, "fpr:::::::::0123456789ABCDEF:\n", "")
        if "--decrypt" in cmd:
            Path(cmd[cmd.index("--output")+1]).write_bytes(b"Synthetic public portfolio message. No surveillance or personal data.\n")
            return subprocess.CompletedProcess(cmd, 0, "[GNUPG:] DECRYPTION_OKAY", "")
        if "--verify" in cmd:
            bad = "tampered.txt" in cmd[-1]
            return subprocess.CompletedProcess(cmd, 1 if bad else 0, "[GNUPG:] BADSIG" if bad else "[GNUPG:] VALIDSIG", "")
        return subprocess.CompletedProcess(cmd, 0, "gpg (GnuPG) test-double\n", "")
    def test_orchestration_with_fake_gpg(self):
        self.commands = []
        with tempfile.TemporaryDirectory() as folder, patch.object(v.shutil, "which", return_value="gpg"), patch.object(v.subprocess, "run", side_effect=self.fake_run):
            report = v.exercise(Path(folder)/"new")
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["cloud_key_vault"], "not executed")
        for cmd, kwargs in self.commands:
            if "--version" not in cmd: self.assertIn("--homedir", cmd)
            if kwargs.get("input"):
                self.assertNotIn(kwargs["input"].strip(), cmd)
                self.assertIn("--passphrase-fd", cmd)
    def test_tamper_acceptance_fails(self):
        self.commands = []
        def incorrect(cmd, **kwargs):
            result = self.fake_run(cmd, **kwargs)
            if "tampered.txt" in cmd[-1]: return subprocess.CompletedProcess(cmd, 0, "[GNUPG:] VALIDSIG", "")
            return result
        with tempfile.TemporaryDirectory() as folder, patch.object(v.shutil, "which", return_value="gpg"), patch.object(v.subprocess, "run", side_effect=incorrect), self.assertRaises(RuntimeError): v.exercise(Path(folder)/"new")

if __name__ == "__main__": unittest.main()
