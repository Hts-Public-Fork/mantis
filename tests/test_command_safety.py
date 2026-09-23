import subprocess
import pytest
from mantis.utils.common_utils import CommonUtils


@pytest.mark.parametrize("payload", [
    "a.example.com;touch pwned",
    "$(touch pwned).example.com",
    "`touch pwned`.example.com",
    "a.example.com && touch pwned",
    "a.example.com' ; touch pwned; '",
])
def test_format_command_neutralises_shell_metacharacters(tmp_path, payload):
    command = CommonUtils.format_command("echo {input_domain} > {output_file_path}",
                                         input_domain=payload, output_file_path=tmp_path / "out.txt")
    subprocess.run(command, shell=True, cwd=tmp_path, check=True)
    assert not (tmp_path / "pwned").exists()
    assert (tmp_path / "out.txt").read_text().strip() == payload


def test_format_command_inside_larger_token():
    command = CommonUtils.format_command("gitleaks --source {path}/{DOMAIN}/", path="logs/x", DOMAIN="a.com")
    out = subprocess.run(f"printf %s {command.split(' ', 2)[2]}", shell=True, capture_output=True, text=True).stdout
    assert out == "logs/x/a.com/"


@pytest.mark.parametrize("host", ["example.com", "a.b.example.co.uk", "_dmarc.example.com",
                                  "xn--80ak6aa92e.com", "10.0.0.1", "2001:db8::1"])
def test_valid_hosts(host):
    assert CommonUtils.is_valid_host(host)


@pytest.mark.parametrize("host", ["", None, "a.com;id", "$(id).a.com", "`id`.a.com", "a com",
                                  "-oProxyCommand=x", "a.com/path", "http://a.com", "*.a.com"])
def test_invalid_hosts(host):
    assert not CommonUtils.is_valid_host(host)


@pytest.mark.parametrize("value,expected", [
    (None, "null"), ([], "null"), ("CVE-2021-1", "CVE-2021-1"),
    (["cve-2021-1"], "cve-2021-1"), (["CWE-1", "CWE-2"], "CWE-1,CWE-2"),
])
def test_join_ids(value, expected):
    assert CommonUtils.join_ids(value) == expected
