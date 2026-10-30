#!/usr/bin/env python3
"""Assemble a self-contained python310_amd64 tree using hardlinks where possible."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path("/root/windows_python_offline_resources")
DEST = ROOT / "python310_amd64"
SRC_ENV = ROOT / "environments"
SRC_PROJ = ROOT / "project_specific"
SRC_INST = ROOT / "installers"


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def copy_tree_hardlink(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    for dirpath, dirnames, filenames in os.walk(src):
        rel = Path(dirpath).relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in filenames:
            link_or_copy(Path(dirpath) / name, target_dir / name)


def main() -> None:
    dest_rt = DEST / "runtime"
    dest_env = DEST / "environments"
    dest_rt.mkdir(parents=True, exist_ok=True)
    dest_env.mkdir(parents=True, exist_ok=True)

    for name in [
        "python-3.10.11-amd64.exe",
        "python-3.10.11-amd64.exe.asc",
        "python-3.10.11-amd64.exe.sigstore",
        "vc_redist.x64.exe",
    ]:
        src = SRC_INST / name
        if src.exists():
            link_or_copy(src, dest_rt / name)

    env_ids = []
    for d in sorted(SRC_ENV.iterdir()):
        if d.is_dir() and d.name.endswith("_py310"):
            env_ids.append(d.name)
            copy_tree_hardlink(d, dest_env / d.name)
    if (SRC_PROJ / "07b_gpflow_tf_py310").is_dir():
        env_ids.append("07b_gpflow_tf_py310")
        copy_tree_hardlink(SRC_PROJ / "07b_gpflow_tf_py310", dest_env / "07b_gpflow_tf_py310")

    stats = []
    total_wheels = 0
    total_bytes = 0
    for eid in env_ids:
        wh = dest_env / eid / "wheelhouse"
        wheels = list(wh.glob("*.whl")) if wh.is_dir() else []
        size = sum(p.stat().st_size for p in wheels)
        total_wheels += len(wheels)
        total_bytes += size
        stats.append({"id": eid, "wheels": len(wheels), "bytes": size})

    (DEST / "tree_stats_en.json").write_text(
        json.dumps(
            {
                "python": "3.10.11",
                "arch": "amd64",
                "installer": "runtime/python-3.10.11-amd64.exe",
                "environments": stats,
                "env_count": len(stats),
                "wheel_count": total_wheels,
                "total_bytes": total_bytes,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"envs={len(stats)} wheels={total_wheels} bytes={total_bytes}")


if __name__ == "__main__":
    main()
