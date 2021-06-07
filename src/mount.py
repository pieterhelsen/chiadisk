import logging
import os
import subprocess
import re

from abc import ABC
from pathlib import Path
from hurry.filesize import size, alternative

from src.config import Config
from src.disk import Disk


class DiskMounter(ABC):

    def __init__(self, config: Config):
        self._config = config
        self._disk = Disk

    def mount(self, disk: Disk):
        self._disk = disk

        # create mount dir
        self._create_dir()

        # update fstab
        self._update_fstab()

        # mount drive
        self._mount_disk()

    def _create_dir(self):
        # create partition folder, including parents
        # skip if the directory exists
        if not self._disk.mount.exists():
            self._disk.mount.mkdir(parents=True)
            logging.debug(f"Creating mount point: {self._disk.mount}")

    def _update_fstab(self) -> bool:
        fp = Path("/etc/fstab")
        has_duplicates = self._check_fstab_duplicates(fp)

        if not has_duplicates:

            total, used, free = self._disk.size
            pretty_total = size(total, system=alternative)
            defaults = "defaults,auto,users,rw,nofail,noatime 0 0"

            fstr = (
                "\n"
                f"# {self._disk.model} - {pretty_total}\n"
                f"UUID={self._disk.uuid}\t{self._disk.mount}\t{self._disk.format}\t{defaults}"
            )

            if os.getuid() == 0:
                with fp.open('a', encoding='utf-8') as f:
                    f.write(fstr)
                logging.debug(f'Updated /etc/fstab for partition {self._disk.partition}')
            else:
                logging.info('/etc/fstab could not be updated due to permission errors. '
                             'Please paste the lines below in the /etc/fstab file:')
                logging.info(fstr)

    def _mount_disk(self) -> bool:
        try:
            subprocess.check_call(['sudo', 'mount', '-v', self._disk.mount])
            return True
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not mount partition ({self._disk.partition}) - returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return False

    def _check_fstab_duplicates(self, fp: Path) -> bool:
        txt = fp.read_text(encoding='utf-8')
        res = False

        if re.search(str(self._disk.mount), txt):
            logging.debug(f"Found mount point duplicate in /etc/fstab ({self._disk.mount}). Skipping...")
            res = True

        if re.search(str(self._disk.uuid), txt):
            logging.debug(f"Found UUID duplicate in /etc/fstab ({self._disk.uuid}). Skipping...")
            res = True

        return res


