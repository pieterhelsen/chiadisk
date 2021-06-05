import csv
from abc import ABC
from pathlib import Path

from src.config import Config
from src.disk import Disk
from src.format import DiskFormatter
from src.mount import DiskMounter


class DiskManager(ABC):

    def __init__(self, config: Config, formatter: DiskFormatter, mounter: DiskMounter):
        self._config = config.get_disk_config()
        self._formatter = formatter
        self._mounter = mounter

        disks = self._get_disks()
        for disk in disks:
            # format disk
            self._formatter.format(disk)

            # mount disk
            self._mounter.mount(disk)

    def _get_disks(self) -> list[Disk]:
        disklist = Path(self._config.get('list'))
        fp = disklist.open(mode='r', encoding='uft-8')
        reader = csv.DictReader(fp)
        disks = []

        for row in reader:
            disks.append(Disk(row))

        return disks
