#!/usr/bin/env python3
"""Build deterministic PhotoGIMP archives for supported platforms."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".config" / "GIMP" / "3.0"
LINUX_DESKTOP = ROOT / ".local" / "share" / "applications" / "org.gimp.GIMP.desktop"
LINUX_ICONS = ROOT / ".local" / "share" / "icons"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def iter_files(path: Path):
    yield from sorted((item for item in path.rglob("*") if item.is_file()), key=lambda p: p.as_posix())


def add_file(archive: zipfile.ZipFile, source: Path, destination: str) -> None:
    info = zipfile.ZipInfo(destination, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    mode = stat.S_IMODE(source.stat().st_mode)
    info.external_attr = (mode & 0xFFFF) << 16
    archive.writestr(info, source.read_bytes())


def add_tree(archive: zipfile.ZipFile, source: Path, destination: str) -> None:
    for file in iter_files(source):
        add_file(archive, file, f"{destination}/{file.relative_to(source).as_posix()}")


def build_archive(output: Path, platform: str) -> None:
    with zipfile.ZipFile(output, "w") as archive:
        if platform == "linux":
            prefix = "PhotoGIMP-linux"
            add_tree(archive, CONFIG, f"{prefix}/.config/GIMP/3.0")
            add_file(archive, LINUX_DESKTOP, f"{prefix}/.local/share/applications/{LINUX_DESKTOP.name}")
            add_tree(archive, LINUX_ICONS, f"{prefix}/.local/share/icons")
            installer = ROOT / "install.sh"
            if installer.exists():
                add_file(archive, installer, f"{prefix}/install.sh")
        else:
            add_tree(archive, CONFIG, "3.0")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    outputs = {
        "linux": args.output / "PhotoGIMP-linux.zip",
        "windows": args.output / "PhotoGIMP-windows.zip",
        "macos": args.output / "PhotoGIMP-macos.zip",
    }
    for platform, output in outputs.items():
        build_archive(output, platform)

    checksum = args.output / "SHA256SUMS.txt"
    checksum.write_text(
        "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in outputs.values()),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
