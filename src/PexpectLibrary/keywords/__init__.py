import sys
import gc
import re
from pexpect import popen_spawn
from io import StringIO
from robot.api import logger
from psutil import NoSuchProcess
import psutil
import time

from src.PexpectLibrary.const import PEXPECT_TIMEOUT_FOR_LAUNCH_COMMAND


class TerminalInteractionKeywords:

    def __init__(self):
        self.main_process = None
        self.sub_process = None

    def __kill_process_for_error(self):
        self.sub_process.kill()
        psutil.Process(self.main_process.pid).kill()
        self.main_process = None
        logger.error("Process kill under unexpected conditions...")

    def run_command(self, *args):
        try:
            logger.info(f"Launching Command: '{' '.join(args)}'...")
            sign_time = time.perf_counter()
            self.main_process = popen_spawn.PopenSpawn(' '.join(args), encoding='utf-8')
            parent_proc = psutil.Process(self.main_process.pid)

            while (time.perf_counter()) > PEXPECT_TIMEOUT_FOR_LAUNCH_COMMAND:
                if parent_proc.children(recursive=True):
                    self.sub_process = parent_proc.children(recursive=True)[0]
                    break
            self.main_process.logfile = sys.stdout
        except Exception as error:
            self.__kill_process_for_error()
            self.main_process = None
            raise Exception(f"Launching Command is failure!{error}")
