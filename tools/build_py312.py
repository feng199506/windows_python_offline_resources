#!/usr/bin/env python3
"""Download a complete python312_amd64 Windows offline tree."""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_environments import ENVIRONMENTS, ENV_ROOT, ROOT  # noqa: E402
from expand_categories import NEW_ENVIRONMENTS, download_one_spec  # noqa: E402
from prepare_environments import (  # noqa: E402
    download_wheels,
    lockfile_from_wheels,
    marker_path,
    write_requirements,
    write_scripts,
    write_wheel_manifest,
)

DEST = ROOT / "python312_amd64"
ENV_DIR = DEST / "environments"
RT_DIR = DEST / "runtime"
STATE = ROOT / "state"


def clone_312(spec: dict) -> dict:
    s = copy.deepcopy(spec)
    s["id"] = spec["id"].replace("_py310", "_py312")
    s["py"] = "312"
    s["root"] = ENV_DIR
    note = s.get("purpose_cn", "")
    if "3.13" in note:
        s["purpose_cn"] = note.replace("3.13", "3.12")
    return s


def prepare(spec: dict) -> dict:
    d = spec["root"] / spec["id"]
    d.mkdir(parents=True, exist_ok=True)
    mark = d / "DOWNLOAD_STATUS_en.json"
    if mark.exists():
        prev = json.loads(mark.read_text(encoding="utf-8"))
        if prev.get("status") == "downloaded" and (d / "wheelhouse").exists():
            print("SKIP", spec["id"])
            n, total, _ = write_wheel_manifest(spec)
            return {**prev, "wheel_count": n, "total_bytes": total, "status": "skipped_existing"}
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_scripts(spec)
    failed = []
    ok, detail = download_wheels(spec, spec["packages"])
    resolved = list(spec["packages"])
    if not ok:
        print(spec["id"], "group failed, per-package")
        resolved = []
        for pkg in spec["packages"]:
            pok, pdetail = download_one_spec(spec, pkg)
            if pok:
                resolved.append(pkg)
                print("  OK", pkg)
            else:
                failed.append({"package": pkg, "detail": (pdetail or "")[-600:]})
                print("  FAIL", pkg)
        write_requirements(spec, resolved or spec["packages"])
    n, total, _ = write_wheel_manifest(spec)
    if n:
        lockfile_from_wheels(spec)
        status = "downloaded"
    else:
        status = "failed"
    result = {
        "environment": spec["id"],
        "status": status,
        "python": "312",
        "direct_ok": resolved,
        "failed": failed,
        "wheel_count": n,
        "total_bytes": total,
        "started_utc": started,
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    mark.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main() -> int:
    ENV_DIR.mkdir(parents=True, exist_ok=True)
    RT_DIR.mkdir(parents=True, exist_ok=True)
    inst = ROOT / "installers"
    for name in [
        "python-3.12.10-amd64.exe",
        "python-3.12.10-amd64.exe.asc",
        "python-3.12.10-amd64.exe.sigstore",
        "vc_redist.x64.exe",
    ]:
        src = inst / name
        if src.exists():
            link_or_copy(src, RT_DIR / name)

    specs = []
    for spec in ENVIRONMENTS:
        if spec.get("py") == "310":
            specs.append(clone_312(spec))
    for spec in NEW_ENVIRONMENTS:
        specs.append(clone_312(spec))

    results = []
    for spec in specs:
        print("\n=====", spec["id"], "=====")
        results.append(prepare(spec))
        (STATE / "py312_last.json").write_text(
            json.dumps({k: v for k, v in results[-1].items() if k != "failed"}, indent=2),
            encoding="utf-8",
        )
    (STATE / "py312_results_en.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for r in results:
        print(f"{r['environment']}: {r['status']} wheels={r['wheel_count']} failed={len(r.get('failed') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
