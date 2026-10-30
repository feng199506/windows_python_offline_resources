#!/usr/bin/env python3
"""Download Windows supplement artifacts only. Does not modify original lockfiles.
Does not build wheels, install, import, or treat Linux wheels as Windows wheels.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path("/root/windows_python_offline_resources")
TOOLS = ROOT / "tools"
PIP = [sys.executable, str(TOOLS / "pip.pyz")]
CACHE = ROOT / "supplement_cache"
LOG = ROOT / "state" / "supplement_download_en.log"
UA = "windows-python-offline-supplement/1.0"

PY310 = ROOT / "python310_amd64_supplement"
PY312 = ROOT / "python312_amd64_supplement"

PLAYWRIGHT_REV = {
    "chromium": "1248",
    "chromium-headless-shell": "1248",
    "firefox": "1555",
    "webkit": "2370",
    "ffmpeg": "1013",
}
PW_HOST = "https://playwright.azureedge.net"


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, expected_sha: str | None = None) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        log(f"SKIP exists {dest.name} ({dest.stat().st_size})")
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    log(f"GET {url} -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r, tmp.open("wb") as f:
        shutil.copyfileobj(r, f)
    tmp.replace(dest)
    digest = sha256_file(dest)
    if expected_sha and digest.lower() != expected_sha.lower():
        raise RuntimeError(f"SHA256 mismatch {dest.name}: {digest} != {expected_sha}")
    log(f"OK {dest.name} bytes={dest.stat().st_size} sha256={digest}")
    return dest


def pip_download(dest: Path, args: list[str]) -> subprocess.CompletedProcess:
    dest.mkdir(parents=True, exist_ok=True)
    cmd = PIP + ["download", "--disable-pip-version-check", "--isolated", "--dest", str(dest)] + args
    log("RUN " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    (dest / "pip_download_log_en.txt").write_text(
        p.stdout + "\n" + p.stderr, encoding="utf-8"
    )
    if p.returncode != 0:
        log(f"FAIL pip download rc={p.returncode}: {(p.stderr or p.stdout)[-800:]}")
    else:
        log(f"OK pip download dest={dest}")
    return p


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def copy_tree_files(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    for p in src.rglob("*"):
        if p.is_file():
            link_or_copy(p, dst / p.relative_to(src))


def write_inventory(dest: Path, rows: list[dict]) -> None:
    fields = [
        "relative_path", "bytes", "sha256", "kind", "version", "source_url",
        "applies_to_envs", "windows_ready", "notes_cn",
    ]
    path = dest / "inventory_cn.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def collect_rows(dest: Path, kind_map: dict[str, tuple[str, str, str, str, str]]) -> list[dict]:
    rows = []
    for p in sorted(dest.rglob("*")):
        if not p.is_file():
            continue
        if p.name in {"inventory_cn.csv"}:
            continue
        rel = str(p.relative_to(dest)).replace("\\", "/")
        kind, ver, url, envs, notes = kind_map.get(rel, ("other", "", "", "", ""))
        if not kind:
            if "/packages_sdist/" in f"/{rel}" or rel.startswith("packages_sdist/"):
                kind, notes = "sdist", "源码包；未在 Windows 上构建 wheel"
            elif rel.startswith("packages_wheel/") or "/packages_wheel/" in f"/{rel}":
                kind, notes = "wheel", "Windows 兼容 wheel（补充锁定，未改原 lock）"
            elif rel.startswith("external/"):
                kind = "external_tool"
        ready = "yes" if kind in {"wheel", "external_tool"} and "sdist" not in kind else "no_until_windows_build"
        if kind == "external_tool":
            ready = "downloaded_not_runtime_verified"
        if kind == "wheel":
            ready = "wheel_present_not_installed"
        rows.append({
            "relative_path": rel,
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p) if p.stat().st_size < 400_000_000 else sha256_file(p),
            "kind": kind,
            "version": ver,
            "source_url": url,
            "applies_to_envs": envs,
            "windows_ready": ready,
            "notes_cn": notes,
        })
    return rows


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    sdist_dir = CACHE / "sdist"
    build_sdist = CACHE / "build_sdist"
    ak_dir = CACHE / "akshare310"
    ext = CACHE / "external"

    # 1) sdists for missing pure-python packages
    r = pip_download(
        sdist_dir,
        ["--no-binary", ":all:", "--no-deps", "lime", "ta", "jieba", "odfpy"],
    )
    if r.returncode != 0:
        log("sdist group failed, trying per package")
        for pkg in ["lime", "ta", "jieba", "odfpy"]:
            pip_download(sdist_dir, ["--no-binary", ":all:", "--no-deps", pkg])

    pip_download(
        build_sdist,
        ["--no-binary", ":all:", "--no-deps", "setuptools", "wheel", "build", "packaging", "pip"],
    )

    # extra runtime deps that are sdist-only (defusedxml is usually a wheel already)
    pip_download(sdist_dir, ["--no-binary", ":all:", "--no-deps", "defusedxml"])

    # 2) akshare historical for 3.10
    ak = pip_download(
        ak_dir,
        [
            "--platform", "win_amd64",
            "--python-version", "310",
            "--implementation", "cp",
            "--only-binary", ":all:",
            "akshare==1.18.88",
        ],
    )
    pip_download(sdist_dir, ["--no-binary", ":all:", "--no-deps", "akshare==1.18.88"])
    ak_ok = ak.returncode == 0
    (CACHE / "akshare310_status.json").write_text(
        json.dumps({"ok": ak_ok, "version": "1.18.88", "requires_python": ">=3.9",
                    "reason": "" if ak_ok else (ak.stderr or "")[-1500:]}, indent=2),
        encoding="utf-8",
    )

    # 3) externals
    ffmpeg_sha = urllib.request.urlopen(
        urllib.request.Request(
            "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip.sha256",
            headers={"User-Agent": UA},
        ),
        timeout=60,
    ).read().decode().strip().split()[0]
    download(
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
        ext / "ffmpeg" / "ffmpeg-release-essentials.zip",
        ffmpeg_sha,
    )
    (ext / "ffmpeg" / "ffmpeg-release-essentials.zip.sha256").write_text(ffmpeg_sha + "\n", encoding="utf-8")
    (ext / "ffmpeg" / "SOURCE_en.txt").write_text(
        "https://www.gyan.dev/ffmpeg/builds/\nredirects to ffmpeg-9.0.2-essentials_build.zip\n"
        "Listed by https://ffmpeg.org/download.html as Windows builds from gyan.dev\n",
        encoding="utf-8",
    )

    download(
        "https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe",
        ext / "tesseract" / "tesseract-ocr-w64-setup-5.4.0.20240606.exe",
    )
    for lang in ["eng", "chi_sim", "chi_tra", "osd"]:
        download(
            f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/{lang}.traineddata",
            ext / "tesseract" / "tessdata_fast" / f"{lang}.traineddata",
        )
    (ext / "tesseract" / "SOURCE_en.txt").write_text(
        "Installer: UB-Mannheim Tesseract 5.4.0.20240606 win64\n"
        "https://github.com/UB-Mannheim/tesseract/releases/tag/v5.4.0.20240606\n"
        "Language data: tessdata_fast eng/chi_sim/chi_tra/osd\n"
        "https://github.com/tesseract-ocr/tessdata_fast\n",
        encoding="utf-8",
    )

    for name, rev in PLAYWRIGHT_REV.items():
        fn = f"{name}-win64.zip"
        download(
            f"{PW_HOST}/builds/{name}/{rev}/{fn}",
            ext / "playwright_browsers" / fn,
        )
    (ext / "playwright_browsers" / "SOURCE_en.txt").write_text(
        "Playwright 1.64.1 browsers.json revisions (win64)\n"
        + json.dumps(PLAYWRIGHT_REV, indent=2)
        + "\nHost: https://playwright.azureedge.net/builds/<name>/<rev>/<name>-win64.zip\n"
        "Matches python310/312 environments/22b_playwright_py3xx (playwright==1.64.1)\n",
        encoding="utf-8",
    )

    chrome_ver = "156.0.8078.80"
    download(
        f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_ver}/win64/chrome-win64.zip",
        ext / "chrome_for_testing" / "chrome-win64.zip",
    )
    download(
        f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_ver}/win64/chromedriver-win64.zip",
        ext / "chrome_for_testing" / "chromedriver-win64.zip",
    )
    (ext / "chrome_for_testing" / "SOURCE_en.txt").write_text(
        f"Chrome for Testing Stable {chrome_ver} win64 + matching chromedriver\n"
        "https://googlechromelabs.github.io/chrome-for-testing/\n"
        "For Selenium 4.52 in 22_crawler (not Playwright).\n",
        encoding="utf-8",
    )

    meta = {
        "ffmpeg": "9.0.2 essentials (gyan.dev)",
        "tesseract": "5.4.0.20240606",
        "chrome": chrome_ver,
        "playwright": "1.64.1",
        "akshare310": "1.18.88" if ak_ok else "FAILED",
        "akshare310_ok": ak_ok,
    }
    (CACHE / "versions_en.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    log("downloads done " + json.dumps(meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
