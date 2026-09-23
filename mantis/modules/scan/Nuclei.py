import json
import logging
from mantis.utils.crud_utils import CrudUtils
from mantis.models.args_model import ArgsModel
from mantis.utils.common_utils import CommonUtils
from mantis.tool_base_classes.toolScanner import ToolScanner
from mantis.utils.tool_utils import get_assets_with_non_empty_fields, get_assets_with_empty_fields
from mantis.config_parsers.config_client import ConfigProvider

'''
Nuclei Module is running the nuclei scans excluding technology scan
Output: JSON file
Information inserted into DB:
- Title
- Description
- Severity 
- CVE ID
- CWE ID
- Host with protocol
'''

class Nuclei(ToolScanner):

    def __init__(self) -> None:
        super().__init__()

    async def get_commands(self,args: ArgsModel):
        self.org = args.org
        whitelist = ConfigProvider.get_config().nuclei_template_path.whitelist
        blacklist = ConfigProvider.get_config().nuclei_template_path.blacklist
        self.base_command = 'nuclei -u {input_domain} -jle {output_file_path} -v -et http/technologies/ -exclude-severity info -hm'
        
        if whitelist is not None:
            whitelist_command = ' -t {}'.format(whitelist)
            self.base_command += whitelist_command
        if blacklist is not None:
            blacklist_command = ' -et {}'.format(blacklist)
            self.base_command += blacklist_command

        self.outfile_extension = ".json"
        self.assets = await get_assets_with_non_empty_fields(self, args, "active_hosts")
        self.assets.extend(await get_assets_with_empty_fields(self, args, "active_hosts"))

        for every_asset in self.assets:
            if "_id" in every_asset:
                domain = every_asset["_id"]
                # One run per asset so the Open/Fixed reconciliation sees all of its findings
                targets = ",".join(every_asset["active_hosts"][0])
            else:
                domain = every_asset
                targets = every_asset
            outfile = CommonUtils.generate_unique_output_file_name(domain, self.outfile_extension)
            command = CommonUtils.format_command(self.base_command, input_domain = targets, output_file_path = outfile)
            self.commands_list.append((self, command, outfile, domain))

        return self.commands_list
    
    def parse_report(self, outfile):
        report_dict = []
        nuclei_info = []
        self.finding_type = "vulnerability"
        # Convert json lines file to dict
        with open(outfile) as json_lines:
            for line in json_lines:
                report_dict.append(json.loads(line))
        if report_dict:
            for every_vuln in report_dict:
                nuclei = {}
                logging.debug(f'Every vulnerability - {every_vuln}')
                nuclei["type"] = "vulnerability"
                nuclei["org"] = self.org
                nuclei['title'] = every_vuln['template-id']

                info = every_vuln.get('info', {})
                classification = info.get('classification') or {}
                nuclei['description'] = info.get('description') or "null"
                nuclei['info'] = info
                nuclei['severity'] = info.get('severity') or "null"
                nuclei['cve_id'] = CommonUtils.join_ids(classification.get('cve-id'))
                nuclei['cwe_id'] = CommonUtils.join_ids(classification.get('cwe-id'))

                nuclei['host_with_protocol'] = every_vuln['host']

                nuclei['remediation'] = "null"
                
                nuclei_info.append(nuclei)

            return nuclei_info
        else:
            logging.debug('Nuclei output file found, but no vulnerabilities were reported')
    
    async def db_operations(self, output_dict, asset=None):

        await CrudUtils.insert_findings(self, asset, output_dict, self.finding_type)
