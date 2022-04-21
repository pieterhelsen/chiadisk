import argparse
import logging
import subprocess
from argparse import ArgumentParser, Namespace
from pathlib import Path
from time import sleep
from typing import Tuple

from src.config import Config
from src.disk import Disk
from src.format import DiskFormatter
from src.manager import DiskManager
from src.mount import DiskMounter
from src.sheet import DiskSheet


def parse_arguments() -> Tuple[ArgumentParser, Namespace]:
    parser = argparse.ArgumentParser(
        description="diskman: Disk formatter and health checker."
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--add', type=str, help="path to newly added disk")
    group.add_argument('--config', type=str, help="path to config, defaults to config.yaml")
    group.add_argument('--version', action='store_true')
    return parser, parser.parse_args()


def set_config() -> Config:
    conf = Config(Path(args.config)) if args.config is not None else Config(Path("config.yaml"))

    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
        level=conf.get_log_level(),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return conf


def add(path: Path):
    config = set_config()
    disk = Disk(str(path))

    # Disk Formatter - formats disks
    formatter = DiskFormatter(config)
    formatter.format(disk)

    # Disk Sheet - adds disk to Google Sheet
    sheet = DiskSheet()
    sheet.init(config)
    sheet.add(disk)


def init():
    config = set_config()
    logging.info(f"Starting diskman ({version()})")

    # Disk Manager -
    manager = DiskManager(config)

    while True:
        manager.check()
        sleep(config.get_interval())


def version():
    try:
        command_args = ["git", "describe", "--tags"]
        f = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = f.communicate()
        return stdout.decode(encoding="utf-8").rstrip()
    except:
        return "unknown"


if __name__ == "__main__":
    # Parse config
    global argparse, args
    argparse, args = parse_arguments()

    if args.version:
        print(version())
    elif args.add:
        add(Path(args.add))
    else:
        init()

