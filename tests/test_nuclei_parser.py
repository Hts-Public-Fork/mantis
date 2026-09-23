import json
from mantis.modules.scan.Nuclei import Nuclei
from mantis.modules.scan.NucleiInfo import NucleiInfo

FINDING = {
    "template-id": "CVE-2021-44228",
    "host": "https://a.example.com",
    "info": {
        "name": "Log4j RCE",
        "severity": "critical",
        "description": "Apache Log4j2 JNDI RCE",
        "classification": {"cve-id": ["cve-2021-44228"], "cwe-id": ["cwe-502"]},
    },
}


def _write(tmp_path, *findings):
    outfile = tmp_path / "nuclei.json"
    outfile.write_text("\n".join(json.dumps(f) for f in findings))
    return str(outfile)


def test_nuclei_extracts_description_cve_and_cwe(tmp_path):
    scanner = Nuclei()
    scanner.org = "org"
    [finding] = scanner.parse_report(_write(tmp_path, FINDING))
    assert finding["description"] == "Apache Log4j2 JNDI RCE"
    assert finding["severity"] == "critical"
    assert finding["cve_id"] == "cve-2021-44228"
    assert finding["cwe_id"] == "cwe-502"
    assert finding["host_with_protocol"] == "https://a.example.com"


def test_nuclei_handles_missing_classification(tmp_path):
    minimal = {"template-id": "x", "host": "https://a.example.com", "info": {"severity": "low"}}
    scanner = NucleiInfo()
    scanner.org = "org"
    [finding] = scanner.parse_report(_write(tmp_path, minimal))
    assert finding["description"] == "null"
    assert finding["cve_id"] == "null"
    assert finding["cwe_id"] == "null"
