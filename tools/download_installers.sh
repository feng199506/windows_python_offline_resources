#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/installers"
META="$DEST/download_meta_cn.csv"
mkdir -p "$DEST" "$ROOT/tools" "$ROOT/state"

download() {
  local url="$1"
  local out="$2"
  echo "DOWNLOAD $url -> $out"
  curl -L --fail --retry 5 --retry-delay 2 --continue-at - --output "$out" "$url"
}

# Portable pip zipapp (used only as a downloader on this Linux host; not installed into system Python)
download "https://bootstrap.pypa.io/pip/pip.pyz" "$ROOT/tools/pip.pyz"

# Python 3.10.11 Windows x64 full installer (last 3.10 release with binary installer)
download "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe" "$DEST/python-3.10.11-amd64.exe"
download "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe.asc" "$DEST/python-3.10.11-amd64.exe.asc" || true
download "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe.sigstore" "$DEST/python-3.10.11-amd64.exe.sigstore" || true

# Python 3.13.17 Windows x64 full installer (last 3.13 security release that still ships installers)
download "https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe" "$DEST/python-3.13.17-amd64.exe"
download "https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe.asc" "$DEST/python-3.13.17-amd64.exe.asc" || true
download "https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe.sigstore" "$DEST/python-3.13.17-amd64.exe.sigstore" || true

# Microsoft Visual C++ Redistributable x64 (VS 2015-2022 standalone offline installer)
download "https://aka.ms/vs/17/release/vc_redist.x64.exe" "$DEST/vc_redist.x64.exe"

# Git for Windows 64-bit full installer (not MinGit, not portable 7z)
download "https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.4/Git-2.56.0.4-64-bit.exe" "$DEST/Git-2.56.0.4-64-bit.exe"

python3 - <<'PY'
import csv, hashlib, os, struct
from pathlib import Path

root = Path("/root/windows_python_offline_resources/installers")
rows = []

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def authenticode_info(p: Path) -> str:
    """Best-effort Authenticode directory presence; signer CN if PKCS7 can be parsed."""
    try:
        data = p.read_bytes()
    except OSError:
        return "unreadable"
    if data[:2] != b"MZ":
        return "not_pe"
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe+4] != b"PE\x00\x00":
        return "not_pe"
    magic = struct.unpack_from("<H", data, pe + 24)[0]
    if magic == 0x20B:  # PE32+
        dd_off = pe + 24 + 112
    elif magic == 0x10B:  # PE32
        dd_off = pe + 24 + 96
    else:
        return "unknown_pe"
    cert_rva, cert_size = struct.unpack_from("<II", data, dd_off + 4 * 8)
    if cert_size == 0:
        return "no_certificate_table"
    # Certificate table is a file offset, not RVA
    if cert_rva + 8 > len(data):
        return f"certificate_table_present size={cert_size} offset={cert_rva} (truncated)"
    dw_length, w_revision, w_cert_type = struct.unpack_from("<IHH", data, cert_rva)
    return (
        f"certificate_table_present size={cert_size} offset={cert_rva} "
        f"dwLength={dw_length} wRevision={w_revision} wCertificateType={w_cert_type} "
        f"(WIN_CERT_TYPE_PKCS_SIGNED_DATA=2 expected; signer CN requires Windows signtool/osslsigncode)"
    )

known = [
    {
        "file": "python-3.10.11-amd64.exe",
        "product": "CPython 3.10.11 Windows x64 full installer",
        "version": "3.10.11",
        "arch": "x86-64",
        "source": "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe",
        "official_page": "https://www.python.org/downloads/release/python-31011/",
        "official_md5": "a55e9c1e6421c84a4bd8b4be41492f51",
        "official_sha256": "",
        "notes": "Last 3.10 release that published Windows/macOS binary installers. Later 3.10.x are source-only. Python 3.10 reached end of life on 2026-10-01.",
    },
    {
        "file": "python-3.12.10-amd64.exe",
        "product": "CPython 3.12.10 Windows x64 full installer",
        "version": "3.12.10",
        "arch": "x86-64",
        "source": "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe",
        "official_page": "https://www.python.org/downloads/release/python-31210/",
        "official_md5": "5eddb0b6f12c852725de071ae681dde4",
        "official_sha256": "",
        "notes": "Last 3.12 release that published Windows/macOS binary installers. Later 3.12.x are source-only security fixes. Security support until 2028-10.",
    },
    {
        "file": "python-3.13.17-amd64.exe",
        "product": "CPython 3.13.17 Windows x64 full installer",
        "version": "3.13.17",
        "arch": "x86-64",
        "source": "https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe",
        "official_page": "https://www.python.org/downloads/release/python-31317/",
        "official_md5": "",
        "official_sha256": "5da012101ba2e17113a9a1cd901e9ce1441086f2b7ecb5de06ec94163899a190",
        "notes": "Last 3.13 security release that still ships Windows installers as of this download. 3.13.18 is source-only. Security support until 2029-10.",
    },
    {
        "file": "vc_redist.x64.exe",
        "product": "Microsoft Visual C++ Redistributable x64 (VS 2015-2022)",
        "version": "latest from aka.ms/vs/17/release at download time",
        "arch": "x86-64",
        "source": "https://aka.ms/vs/17/release/vc_redist.x64.exe",
        "official_page": "https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist",
        "official_md5": "",
        "official_sha256": "",
        "notes": "Standalone offline redistributable, not a Visual Studio bootstrapper.",
    },
    {
        "file": "Git-2.56.0.4-64-bit.exe",
        "product": "Git for Windows 64-bit installer",
        "version": "2.56.0.windows.4",
        "arch": "x86-64",
        "source": "https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.4/Git-2.56.0.4-64-bit.exe",
        "official_page": "https://github.com/git-for-windows/git/releases/tag/v2.56.0.windows.4",
        "official_md5": "",
        "official_sha256": "4961a4a8cc778d8b6e00a5819e5fe4d078b754555aff7aedc2d77a5d74c2de80",
        "notes": "Full Git for Windows installer. Not MinGit and not the portable 7z package.",
    },
]

out_csv = root / "installer_inventory_cn.csv"
fields = [
    "file", "product", "version", "arch", "bytes", "sha256", "official_sha256",
    "official_md5", "sha256_match", "source", "official_page", "authenticode", "notes",
]
with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for item in known:
        p = root / item["file"]
        row = dict(item)
        if p.exists():
            row["bytes"] = p.stat().st_size
            digest = sha256(p)
            row["sha256"] = digest
            official = item.get("official_sha256") or ""
            row["sha256_match"] = (
                "match" if official and official.lower() == digest.lower()
                else ("not_published_on_page" if not official else "MISMATCH")
            )
            row["authenticode"] = authenticode_info(p)
        else:
            row["bytes"] = ""
            row["sha256"] = ""
            row["sha256_match"] = "missing"
            row["authenticode"] = "missing"
        w.writerow({k: row.get(k, "") for k in fields})
        print(f"{item['file']}: exists={p.exists()} size={row.get('bytes')} sha256={row.get('sha256')}")
print(f"Wrote {out_csv}")
PY

echo "Installer download finished."
ls -lh "$DEST"
ls -lh "$ROOT/tools/pip.pyz"
