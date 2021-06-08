import csv
import logging
from abc import ABC
from pathlib import Path
from typing import List

from src.config import Config
from src.disk import Disk
from src.format import DiskFormatter
from src.mount import DiskMounter


class DiskManager(ABC):

    def __init__(self, config: Config, formatter: DiskFormatter, mounter: DiskMounter):
        self._config = config.get_disk_config()
        self._formatter = formatter
        self._mounter = mounter

        logging.info(f"Starting Disk List readout")

        disks = self._get_disks()
        logging.info("------------------------------------------------------------------------")
        logging.info(f"Found {len(disks)} disks for processing.")

        for disk in disks:
            logging.info("------------------------------------------------------------------------")
            logging.info(f"Starting setup process for disk {disk.device} (mounting to {disk.mount}")

            # format disk
            self._formatter.format(disk)

            # mount disk
            self._mounter.mount(disk)

    def _get_disks(self) -> List[Disk]:
        disklist = Path(self._config.get('list'))
        fp = disklist.open(mode='r', encoding='utf-8', newline='')
        reader = csv.DictReader(fp, delimiter=';')
        disks = []

        for row in reader:
            disks.append(Disk(row, disklist))

        return disks
