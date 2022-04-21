# Diskman
Disk formatter and health checker

## !! Warning !! this is an experimental tool. Use at your own risk.

This utility is a disk manager for [Chia](https://www.chia.net/) farmers. It is by no means completed yet and a lot of 
features will likely still be improved upon in the future. These are the
functions that I envisioned as part of this tool:

- Disk formatting (**done**)
- Disk cataloguing (**done**)  
- Disk mounting (via `/etc/fstab`) (**done**)
- Adding mounted disk to Chia (**in progress**)
- Checking disk health (**todo**)

**Note**: this tool is intended for use on Linux systems **ONLY**.

# Todo

The following is still on the todo list:

- Improve overall code quality
- Add `black`, `flake8` and `mypy` linters, formatters and code checkers.
- Add unit tests
- Add compatibility with other formats than `ext4` (such as `ntfs`)  
- The tool currently requires you to run it as `sudo`, in the future, I hope to implement a better way for this.
- Add additional features described above


# Usage

### Clone the repository

In order to use diskman, checkout the program using git:

```
$ git clone https://github.com/pieterhelsen/diskman 
```

### Create Disklist

Next, copy the disklist-example.csv to a file ready for editing.

```
$ cd diskman
$ cp disklist-example.csv disklist.csv
$ nano disklist.csv
```

This csv file contains 7 columns:

- `device`: the base path for your drive. Eg. `/dev/sda` (**not** the partition path)
- `mount`: the mount point where you want to disk to be mounted
- `clear`: this one's important! If you want your disk to be formatted, write 'yes' or 'y' here. Any other value will
be interpreted as 'no, I don't want to format this disk.'
- `format`: the format you'd like your disk to have. **Currently only tested with ext4**
- `sn`: the serial number for the disk. Leave this blank, as diskman will fill this in automatically.
- `model`: the model ID for the disk. Leave this blank, as diskman will fill this in automatically.
- `uuid`: the UUID of the **first** partition of the disk. Leave this blank, diskman will fill in this value
  automatically. 
  
Make sure to fill in the `device`, `mount`, `clear` and `format` columns.
I also recommend testing the tool first with a single line. 

Now save the file and move to the next step. 

### Update Config

Now make a copy of the `config-example.yaml`

```
$ cp config-example.yaml config.yaml
$ nano config.yaml
```

You probably won't need to update any variables in the reference config for now. 
The `chiapath` variable will be used to add your plot paths to Chia. However, this process currently does not work yet. 

Alright, you're done! Time to give the script a go:

```
$ sudo ./venv/bin/python3 diskman.py --config config.yaml
```

# Thoughts

Refactor to a more barebones approach where:

- `diskman --add` allows you to specify a newly added drive and optionally format it.
- `diskman` will run as a `systemd` service that periodically checks a Google Sheet for changes (from diskman add), updates `/etc/fstab`, mounts the volumes and adds them to `chia plots add`

- add
  - format disk
  - commit disk to sheet (serial number, model number, family??, partition, rotation, disk id, harvester id)
  - mount disk (+ chown?)
- init
  - create mount points
  - update chia config
  - update /etc/fstab.d/01_chia.fstab
  - mount fstab.d folder (https://manpages.ubuntu.com/manpages/xenial/man8/mount.8.html --fstab)

# Contributing

Contributions are always welcome! Please refer to [CONTRIBUTING](CONTRIBUTING.md) documentation.