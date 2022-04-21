import csv
import logging
from abc import ABC
from pathlib import Path
from typing import List

from src.config import Config
from src.disk import Disk
from src.format import DiskFormatter
from src.mount import DiskMounter
from src.sheet import DiskSheet


class DiskManager(ABC):

    def __init__(self, config: Config):
        self._config = config.get_disk_config()

        self._mounter = DiskMounter(config)
        self._sheet = DiskSheet
        self._sheet.init(config=config)
        self._sheet.get_disks()

        logging.info(f"Starting Disk List readout")

        logging.info("------------------------------------------------------------------------")
        logging.info(f"Found {len(disks)} disks for processing.")

        for disk in disks:
            logging.info("------------------------------------------------------------------------")
            logging.info(f"Starting setup process for disk {disk.path} (mounting to {disk.mount}")

            # mount disk
            self._mounter.mount(disk)

    def check(self):
        #do something
        pass

