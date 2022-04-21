from pathlib import Path


class MountPoint:

    def __init__(self, base_mount:str, max_index: int = 0):
        self.base_mount = base_mount
        self.max = max_index

    def __iter__(self):
        self.n = self.max
        return self

    def __next__(self) -> Path:
        if self.n >= 0:
            result = f"{self.base_mount}{str(self.n).zfill(len(str(self.max)))}"
            self.n -= 1
            return Path(result)
        else:
            raise StopIteration
