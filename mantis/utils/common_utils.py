import os
import re
import pytz
import shlex
import uuid
import logging
import datetime
from ipaddress import ip_address
from mantis.config_parsers.config_client import ConfigProvider

HOSTNAME_REGEX = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9_](?:[A-Za-z0-9_-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z0-9-]{2,63}$"
)


class CommonUtils:

    @staticmethod
    def format_command(template: str, **kwargs) -> str:
        # Shell-quote every interpolated value so attacker-influenced assets
        # (subdomains from Wayback, VirusTotal, CT logs etc.) can't inject commands
        quoted = {key: shlex.quote(str(value)) for key, value in kwargs.items()}
        return template.format(**quoted)

    @staticmethod
    def join_ids(value) -> str:
        # Nuclei classification ids (cve-id, cwe-id) may be a list, a string or null
        if not value:
            return "null"
        if isinstance(value, str):
            return value
        return ",".join(str(v) for v in value)

    @staticmethod
    def is_valid_host(target) -> bool:
        if not isinstance(target, str) or not target:
            return False
        try:
            ip_address(target)
            return True
        except ValueError:
            return bool(HOSTNAME_REGEX.match(target))

    @staticmethod
    def parse_file(file_name: str) -> list:
        logging.debug(f"file_process() {file_name}")
        try:
            with open(file_name) as file:
                hosts = [line.rstrip() for line in file]
                hosts = [line for line in hosts if line]
                return hosts
        except FileNotFoundError:
            logging.error(f"Input file {file_name} is not found, QUTTING !")
            exit(1)

    @staticmethod
    def get_ikaros_std_timestamp():
        ist =  pytz.timezone('Asia/Kolkata')
        return datetime.datetime.now(ist).isoformat()

    @staticmethod
    def strip_url_scheme(target):
        target=target.replace('http://','')
        target=target.replace('https://','')
        if target[-1] == "/":
            target = target[:-1]
        logging.debug(f"Post strip_chars {target}")
        return target

    @staticmethod
    def generate_unique_output_file_name(domain, extension):
        outputDir = 'logs/tool_logs/'
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
        outfile = outputDir + str(uuid.uuid4()) + extension
        return outfile
    