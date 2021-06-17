import logging
import os
import shutil
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
        self._fstab = Path('/etc/fstab')
        self._backup_fstab()

    def mount(self, disk: Disk):
        self._disk = disk

        # create mount dir
        self._create_dir()

        # update fstab
        self._update_fstab()

        # mount drive
        self._mount_disk()

        # add to chia
        self._add_chia_disk()

    def _create_dir(self):
        # create partition folder, including parents
        # skip if the directory exists
        if not self._disk.mount.exists():
            self._disk.mount.mkdir(parents=True)
            logging.info(f"Creating mount point: {self._disk.mount}")
        else:
            logging.debug(f"Mount point exists: {self._disk.mount}")

    def _update_fstab(self) -> bool:
        has_duplicates = self._check_fstab_duplicates()

        if not has_duplicates:

            total, used, free = self._disk.size
            pretty_total = size(total, system=alternative)
            defaults = "defaults,auto,users,rw,nofail,noatime 0 0"

            fstr = (
                "\n"
                f"# {self._disk.model} - {pretty_total}\n"
                f"UUID=\"{self._disk.uuid}\"\t{self._disk.mount}\t{self._disk.format}\t{defaults}"
                "\n"
            )

            if os.getuid() == 0:
                with self._fstab.open('a', encoding='utf-8') as f:
                    f.write(fstr)
                logging.debug(f'Updated /etc/fstab for partition {self._disk.partition}')
            else:
                logging.info('/etc/fstab could not be updated due to permission errors. '
                             'Please paste the lines below in the /etc/fstab file:')
                logging.info(fstr)

            return True

        return False

    def _mount_disk(self) -> bool:
        try:
            subprocess.check_call(['sudo', 'mount', '-v', self._disk.mount])
            logging.info(f"Mounted {self._disk.partition} to {self._disk.mount}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not mount partition ({self._disk.partition}) - returncode: {e.returncode}"
            )

        return False

    def _add_chia_disk(self) -> bool:
        if self._find_chia_disk(self._disk.mount):
            return False

        chia = Path(self._config.get_disk_config().get("chiapath", '~/chia-blockchain')) / 'venv/bin/chia'
        try:
            subprocess.check_call([chia, 'plots', 'add', '-d', self._disk.mount])
            logging.info(f"Added {self._disk.mount} to chia plots")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not add mount ({self._disk.mount}) to chia - returncode: {e.returncode}"
            )

        return False

    def _find_chia_disk(self, mount:Path) -> bool:
        chia = Path(self._config.get_disk_config().get("chiapath", '~/chia-blockchain')) / 'venv/bin/chia'
        try:
            command_args = [chia, 'plots', 'show']
            f = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = f.communicate()
            lines = stdout.decode(encoding="utf-8").splitlines()

            for line in lines:
                if line == str(mount):
                    logging.info(f"Mount point ({self._disk.mount}) already exists in chia plots")
                    return True

            return False
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not lookup mount point ({self._disk.mount}) in chia plots - returncode: {e.returncode}"
            )

        return False

    def _backup_fstab(self):
        backup = self._fstab.with_suffix('.bak')
        shutil.copy(self._fstab, backup)

    def _check_fstab_duplicates(self) -> bool:
        txt = self._fstab.read_text(encoding='utf-8')

        if re.search(str(self._disk.mount), txt):
            logging.debug(f"Found mount point duplicate in /etc/fstab ({self._disk.mount}). Skipping...")
            return True

        if re.search(str(self._disk.uuid), txt):
            logging.debug(f"Found UUID duplicate in /etc/fstab ({self._disk.uuid}). Skipping...")
            return True

        return False


