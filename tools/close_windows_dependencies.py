#!/usr/bin/env python3
"""Close Windows transitive dependency gaps left by Linux-hosted pip download.

pip download --platform win_amd64 already pulls the resolver's dependency tree.
This second pass reads each wheel METADATA Requires-Dist, evaluates markers as
Windows + CPython, honors extras requested by other packages, and downloads
any missing binary wheels into the same wheelhouse.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path("/root/windows_python_offline_resources")
PIP_PYZ = ROOT / "tools" / "pip.pyz"
PYTHON = sys.executable

sys.path.insert(0, str(PIP_PYZ))
from pip._vendor.packaging.markers import Marker  # noqa: E402
from pip._vendor.packaging.requirements import Requirement  # noqa: E402
from pip._vendor.packaging.utils import canonicalize_name  # noqa: E402

# Keep CUDA / GPU extras out of CPU environments.
SKIP_EXTRAS = {
    "and-cuda", "cuda", "gpu", "cuda12", "cuda11", "cu118", "cu121", "cu124",
    "cu126", "cudnn", "tensorrt", "nccl",
}


def env_marker_env(py: str, extra: str = "") -> dict:
    major, minor = 3, int(py[1:])
    patch = {"310": "11", "312": "10", "313": "17"}.get(py, "0")
    ver = f"{major}.{minor}.{patch}"
    return {
        "implementation_name": "cpython",
        "implementation_version": ver,
        "os_name": "nt",
        "platform_machine": "AMD64",
        "platform_python_implementation": "CPython",
        "platform_release": "10",
        "platform_system": "Windows",
        "platform_version": "10.0.19045",
        "python_full_version": ver,
        "python_version": f"{major}.{minor}",
        "sys_platform": "win32",
        "extra": extra or "",
    }


def marker_ok(marker_str: str | None, py: str, extra: str = "") -> bool:
    if not marker_str:
        return True
    try:
        return Marker(marker_str).evaluate(env_marker_env(py, extra))
    except Exception:
        # If marker cannot be evaluated, keep the requirement so we do not drop deps.
        return True


def parse_wheel_filename(name: str) -> tuple[str, str]:
    stem = name[:-4]
    parts = stem.split("-")
    if len(parts) < 5:
        return canonicalize_name(parts[0]), parts[1] if len(parts) > 1 else ""
    dist = canonicalize_name(parts[0])
    version = parts[1]
    return dist, version


def read_metadata(path: Path) -> dict:
    info = {
        "name": "",
        "version": "",
        "requires": [],  # list of (Requirement, marker, extras_on_req)
        "provides_extras": set(),
    }
    with zipfile.ZipFile(path) as zf:
        meta_name = next((n for n in zf.namelist() if n.endswith(".dist-info/METADATA")), None)
        if not meta_name:
            return info
        text = zf.read(meta_name).decode("utf-8", errors="replace")
    for ln in text.splitlines():
        if ln.lower().startswith("name:"):
            info["name"] = canonicalize_name(ln.split(":", 1)[1].strip())
        elif ln.lower().startswith("version:"):
            info["version"] = ln.split(":", 1)[1].strip()
        elif ln.lower().startswith("provides-extra:"):
            info["provides_extras"].add(ln.split(":", 1)[1].strip())
        elif ln.lower().startswith("requires-dist:"):
            raw = ln.split(":", 1)[1].strip()
            try:
                req = Requirement(raw)
            except Exception:
                continue
            info["requires"].append(req)
    if not info["name"]:
        dist, ver = parse_wheel_filename(path.name)
        info["name"], info["version"] = dist, ver
    return info


def load_house(wh: Path) -> dict:
    pkgs = {}
    for w in sorted(wh.glob("*.whl")):
        meta = read_metadata(w)
        key = meta["name"] or parse_wheel_filename(w.name)[0]
        pkgs[key] = {"path": w, **meta}
    return pkgs


def extras_from_direct_file(req_file: Path) -> dict[str, set[str]]:
    extras: dict[str, set[str]] = defaultdict(set)
    if not req_file.exists():
        return extras
    for ln in req_file.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        try:
            req = Requirement(s)
        except Exception:
            continue
        extras[canonicalize_name(req.name)] |= set(req.extras)
    return extras


def needed_requirements(pkgs: dict, py: str, activated: dict[str, set[str]]) -> list[Requirement]:
    out = []
    for name, meta in pkgs.items():
        extras = set(activated.get(name, set()))
        extras.add("")  # unconditional deps
        seen = set()
        for extra in extras:
            if extra.lower() in SKIP_EXTRAS:
                continue
            for req in meta["requires"]:
                marker = str(req.marker) if req.marker else None
                # Skip CUDA extras requested of the dependency
                if any(e.lower() in SKIP_EXTRAS for e in req.extras):
                    continue
                if not marker_ok(marker, py, extra):
                    continue
                key = (str(req), extra)
                if key in seen:
                    continue
                seen.add(key)
                out.append(req)
    return out


def close_one(env_path: Path, py: str, index_url: str, extra_index: list[str]) -> dict:
    wh = env_path / "wheelhouse"
    wh.mkdir(parents=True, exist_ok=True)
    direct = env_path / "requirements_direct_en.txt"
    report = {
        "environment": env_path.name,
        "added": [],
        "still_missing": [],
        "skipped_no_wheel": [],
        "rounds": 0,
    }
    for rnd in range(1, 8):
        report["rounds"] = rnd
        pkgs = load_house(wh)
        activated = extras_from_direct_file(direct)
        # extras implied by already-present packages' Requires-Dist
        changed_extras = True
        while changed_extras:
            changed_extras = False
            for req in needed_requirements(pkgs, py, activated):
                dep = canonicalize_name(req.name)
                if req.extras:
                    before = set(activated[dep])
                    activated[dep] |= set(req.extras)
                    if activated[dep] != before:
                        changed_extras = True
        present = set(pkgs)
        missing_reqs = {}
        for req in needed_requirements(pkgs, py, activated):
            dep = canonicalize_name(req.name)
            if dep not in present:
                missing_reqs[dep] = req
        if not missing_reqs:
            break
        # Download missing one-by-one so a single no-wheel package does not abort the rest
        for dep, req in sorted(missing_reqs.items()):
            spec = str(req)
            # Drop extras and environment markers. Markers must be evaluated as
            # Windows/target Python here; the host is Linux CPython 3.14 and would
            # skip python_version < "3.11" / sys_platform == "win32" requirements.
            try:
                r2 = Requirement(spec)
                download_spec = r2.name
                if r2.specifier:
                    download_spec += str(r2.specifier)
            except Exception:
                download_spec = dep
            cmd = [
                PYTHON, str(PIP_PYZ), "download",
                "--platform", "win_amd64",
                "--python-version", py,
                "--implementation", "cp",
                "--only-binary", ":all:",
                "--dest", str(wh),
                "--index-url", index_url,
                "--disable-pip-version-check",
                "--isolated",
                download_spec,
            ]
            for extra in extra_index:
                cmd.extend(["--extra-index-url", extra])
            print("MISSING", env_path.name, download_spec)
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                tail = (proc.stdout or "")[-1500:] + (proc.stderr or "")[-1500:]
                report["skipped_no_wheel"].append({"requirement": spec, "detail": tail[-800:]})
                print("  FAIL", spec.split(";")[0][:80])
            else:
                report["added"].append(download_spec)
                print("  OK", download_spec)
    # final missing list
    pkgs = load_house(wh)
    activated = extras_from_direct_file(direct)
    for req in needed_requirements(pkgs, py, activated):
        dep = canonicalize_name(req.name)
        if req.extras:
            activated[dep] |= set(req.extras)
    for req in needed_requirements(pkgs, py, activated):
        dep = canonicalize_name(req.name)
        if dep not in pkgs:
            report["still_missing"].append(str(req))
    report["wheel_count"] = len(list(wh.glob("*.whl")))
    report["total_bytes"] = sum(p.stat().st_size for p in wh.glob("*.whl"))
    return report


ENV_INDEX = {
    "04_pytorch_cpu_py310": ("https://download.pytorch.org/whl/cpu", ["https://pypi.org/simple"]),
    "04_pytorch_cpu_py313": ("https://download.pytorch.org/whl/cpu", ["https://pypi.org/simple"]),
    "05_gpr_bo_pytorch_py310": ("https://download.pytorch.org/whl/cpu", ["https://pypi.org/simple"]),
    "08_rl_basic_py310": ("https://download.pytorch.org/whl/cpu", ["https://pypi.org/simple"]),
    "09_huggingface_llm_cpu_py310": ("https://download.pytorch.org/whl/cpu", ["https://pypi.org/simple"]),
    "15_dl_pytorch_extra_py310": ("https://download.pytorch.org/whl/cpu", ["https://pypi.org/simple"]),
    "17b_nlp_sentence_transformers_py310": ("https://download.pytorch.org/whl/cpu", ["https://pypi.org/simple"]),
}


def iter_envs(only: set[str] | None = None):
    for d in sorted((ROOT / "environments").iterdir()):
        if only and d.name not in only:
            continue
        if (d / "wheelhouse").is_dir():
            py = "313" if d.name.endswith("py313") else "310"
            yield d, py
    for d in sorted((ROOT / "project_specific").iterdir()):
        if only and d.name not in only:
            continue
        if d.is_dir() and (d / "wheelhouse").is_dir():
            yield d, "310"


def main() -> int:
    only = set(sys.argv[1:]) or None
    reports = []
    for env_path, py in iter_envs(only):
        index, extra = ENV_INDEX.get(env_path.name, ("https://pypi.org/simple", []))
        print(f"\n===== close {env_path.name} py{py} =====")
        reports.append(close_one(env_path, py, index, extra))
    out = ROOT / "state" / "dependency_closure_en.json"
    out.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    csv_path = ROOT / "state" / "dependency_closure_cn.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["environment", "added", "still_missing", "skipped_no_wheel", "wheel_count", "total_bytes", "rounds"])
        w.writeheader()
        for r in reports:
            w.writerow({
                "environment": r["environment"],
                "added": "; ".join(r["added"]),
                "still_missing": "; ".join(r["still_missing"]),
                "skipped_no_wheel": "; ".join(x["requirement"] for x in r["skipped_no_wheel"]),
                "wheel_count": r["wheel_count"],
                "total_bytes": r["total_bytes"],
                "rounds": r["rounds"],
            })
    print("\nWrote", out)
    for r in reports:
        print(f"{r['environment']}: added={len(r['added'])} missing={len(r['still_missing'])} now={r['wheel_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
