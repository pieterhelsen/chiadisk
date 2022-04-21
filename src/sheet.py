import logging
from abc import ABC

import gspread
from gspread.exceptions import APIError
from gspread.utils import ValueInputOption
from pandas import DataFrame
from retry import retry
from retry.api import retry_call

from src.config import Config
from src.disk import Disk


class DiskSheet(ABC):
    _instance = None
    _config = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DiskSheet, cls).__new__(cls)

        return cls._instance

    def init(self, config: Config):
        if self._config is None:
            self._config = config
            self._init_sheet()

    def add(self, disk: Disk):
        add = input(f"Would you like to add the disk to the {self._config.get_spreadsheet()} spreadsheet? (Y/n)")
        if add.lower() in ("yes", "y", ""):

            disk_id = str(self._get_next_disk_id()).zfill(len(str(self._config.get_max_mount())))
            harvester_id = self._config.get_harvester_id()
            next_row = self._get_next_row()

            self.ws.append_row([
                disk.smart.vendor,             # Brand
                "",                            # Series
                "Internal HDD",                # Type
                disk.size,                     # Raw size (in bytes)
                disk.smart.capacity,           # Size (in TB)
                disk.smart.rotation_rate,      # RPM
                "F",                           # Farming disk by default
                disk_id,                       # Disk ID
                harvester_id,                  # Harvester ID
                f'=IF(NOT(ISBLANK(H{next_row})); IF(NOT(ISBLANK(I{next_row})); "harvest" &I{next_row}&H{next_row}; "Not in use"); "N/A")',
                disk.smart.model,              # Model
                disk.smart.serial,             # Serial
                disk.uuid                      # UUID
            ], value_input_option=ValueInputOption.user_entered)

    @retry(APIError, tries=10, delay=5, backoff=30)
    def _init_sheet(self):
        self.api = gspread.service_account()
        self.ss = self.api.open(self._config.get_spreadsheet())
        self.ws = self.ss.worksheet(self._config.get_worksheet())

    def get_disks(self) -> DataFrame:
        result = retry_call(self.ws.get_all_records, tries=10, delay=5, backoff=30)
        return DataFrame(result)

    def _get_last_disk_id(self) -> int:
        disk_id = str(self.ws.cell(self._get_last_row(), 8)).lstrip('0')
        return int(disk_id)

    def _get_next_disk_id(self) -> int:
        return self._get_last_disk_id() + 1

    def _get_last_row(self, cols: int = 2) -> int:
        # looks for empty row based on values appearing in 1st N columns
        columns = self.ws.range(1, 1, self.ws.row_count, cols)
        return max([cell.row for cell in columns if cell.value])

    def _get_next_row(self, cols: int = 2) -> int:
        return self._get_last_row(cols) + 1
