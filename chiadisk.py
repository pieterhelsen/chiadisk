import argparse
import logging
import subprocess
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Tuple

from src.config import Config
from src.format import DiskFormatter
from src.manager import DiskManager
from src.mount import DiskMounter


def parse_arguments() -> Tuple[ArgumentParser, Namespace]:
    parser = argparse.ArgumentParser(
        description="Chiadisk: Disk formatter and health checker."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--config', type=str, help="path to config.yaml")
    group.add_argument('--version', action='store_true')
    return parser, parser.parse_args()


def init(config: Config):
    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
        level=config.get_log_level(),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.info(f"Starting Chiadisk ({version()})")

    # Disk Formatter - formats disks
    formatter = DiskFormatter(config)

    # Disk Mounter - creates mount points and mounts disks
    mounter = DiskMounter(config)

    # Disk Checker - checks disk health

    # Disk Manager - ties it all together
    chiadisk = DiskManager(config, formatter, mounter)


def version():
    try:
        command_args = ["git", "describe", "--tags"]
        f = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = f.communicate()
        return stdout.decode(encoding="utf-8").rstrip()
    except:
        return "unknown"


if __name__ == "__main__":
    # Parse config and configure logger
    argparse, args = parse_arguments()

    if args.config:
        conf = Config(Path(args.config))
        init(conf)
    elif args.version:
        print(version())
