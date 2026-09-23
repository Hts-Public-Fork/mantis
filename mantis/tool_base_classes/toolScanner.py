from mantis.utils.common_utils import CommonUtils
from subprocess import Popen, PIPE, DEVNULL
from mantis.models.args_model import ArgsModel
import logging
import os
import signal
import sys
import time
import asyncio

class ToolScanner:

    # Upper bound (seconds) for a single tool invocation; subclasses can override
    timeout = 7200

    def __init__(self) -> None:
        self.org = None
        self.base_command = None
        self.outfile_extension = None
        self.commands_list = []
        self.assets = []
        self.std = sys.stdout


    async def init(self, args:ArgsModel):
        return await self.get_commands(args=args)
    

    def get_commands(self, args: ArgsModel):
        raise NotImplementedError


    def base_get_commands(self, assets) :
        ## Return the list of commands
        command_list = []
        for every_asset in assets:  
            domain = every_asset
            outfile = CommonUtils.generate_unique_output_file_name(domain, self.outfile_extension)
            command = CommonUtils.format_command(self.base_command, input_domain = domain, output_file_path = outfile)
            command_list.append((self, command, outfile, every_asset))
        self.commands_list = command_list
        return command_list
    
    
    def parse_report(self, outfile):
        raise NotImplementedError
    

    async def db_operations(self, tool_output_dict, asset=None):
        raise NotImplementedError
    

    async def execute(self, tool_tuple):
        results = {}
        command, outfile, asset = tool_tuple[1:]
        logging.debug(f"Executing command - {command}")
        
        if self.std == "PIPE":
            stderr = PIPE
            stdout = PIPE
        else:
            stderr = sys.stderr
            stdout = sys.stdout

        code = 1
        try:
            start = time.perf_counter()

            subprocess_obj = await asyncio.create_subprocess_shell(
                command, stderr=DEVNULL, stdout=DEVNULL, start_new_session=True)
            try:
                output, errors = await asyncio.wait_for(subprocess_obj.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                # Kill the whole process group, not just the wrapping shell
                try:
                    os.killpg(subprocess_obj.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                await subprocess_obj.wait()
                results["exception"] = f"Timed out after {self.timeout}s"
                results["command"] = command
                results["success"] = 0
                results["failure"] = 1
                logging.warning(f"{type(self).__name__} timed out after {self.timeout}s for {asset}")
                # Partial output must not be persisted, it would mark findings as Fixed
                return results
            code = subprocess_obj.returncode

            finish = time.perf_counter()

            results["code"] = code
            results["output"] = output
            results["errors"] = errors
            results["asset"] = asset
            results["command"] = command
            results["success"] = 0
            results["failure"] = 0
            results["command_exec_time"] = round(finish - start, 2)
            logging.debug(f"Subprocess output - Code {code}, Errors {errors}")
            if code == 0: 
                results["success"] += 1
            else:
                results["failure"] += 1
            tool_results_dict = self.parse_report(outfile=outfile)
            results["tool_time_taken"] = CommonUtils.get_ikaros_std_timestamp()
            # if tool_results_dict:
            await self.db_operations(tool_results_dict, asset=asset)
        
        except FileNotFoundError as e:
            logging.debug(f"No file generated for the {asset}")

        except Exception as e:
            results["exception"] = str(e)
            logging.debug(
                f"Error received: {type(e).__name__}: {e} for {asset} in tool {type(self).__name__}")
      
        return results