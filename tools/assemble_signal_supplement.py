#!/usr/bin/env python3
"""Directed signal-processing supplement for Windows/Linux CPython 3.10 and 3.12.

Does not modify original lockfiles, original Release trees, or supplement v1.
Reuses compatible local wheels (hardlink). Downloads only missing artifacts.
Board trees receive matching-arch wheels only; x86-64 binaries are never copied there.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import zipfile
from email.parser import Parser
from pathlib import Path
from urllib.request import Request, urlopen

WIN_ROOT = Path("/root/windows_python_offline_resources")
LIN_ROOT = Path("/root/linux_python_offline_resources")
PIP = WIN_ROOT / "tools" / "pip.pyz"
CACHE = WIN_ROOT / "supplement_signal_cache"
UA = "offline-signal-supplement/1.0"
PYPI = "https://pypi.org/pypi"

# Pins aligned with original 03_signal trees.
PINS = {
    "310": {
        "numpy": "2.2.6",
        "scipy": "1.15.3",
        "PyWavelets": "1.8.0",
        "matplotlib": "3.10.9",
        "contourpy": "1.3.2",
        "fonttools": "4.65.0",
        "kiwisolver": "1.5.1",
        "pillow": "12.3.0",
        "python-dateutil": "3.0.0",
    },
    "312": {
        "numpy": "2.5.4",
        "scipy": "1.18.1",
        "PyWavelets": "1.10.0",
        "matplotlib": "3.11.2",
        "contourpy": "1.4.0",
        "fonttools": "4.68.0",
        "kiwisolver": "1.5.1",
        "pillow": "13.0.0",
        "python-dateutil": "3.0.0",
    },
}
SHARED_PINS = {
    "EMD-signal": "1.10.0",
    "filterpy": "2.0.0",
    "pykalman": "0.11.2",
    "scikit-base": "0.13.2",
    "packaging": "26.3",
    "tqdm": "4.70.1",
    "dill": "0.4.1",
    "multiprocess": "0.70.19",
    "cycler": "0.12.1",
    "pyparsing": "3.3.3",
    "six": "1.17.0",
}

NEW_DIRECT = ["EMD-signal", "filterpy", "pykalman"]
# pathos is required by EMD-signal; scikit-base by pykalman (<0.14).
PATHOS_STACK = ["pathos", "pox", "ppft"]
BUILD_FOR_SDIST = ["setuptools", "wheel", "cython", "meson-python", "ninja", "packaging", "meson"]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.stat().st_ino == src.stat().st_ino or sha256_file(dst) == sha256_file(src):
            return
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def http_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=90) as r:
        return json.load(r)


def http_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=180) as r:
        return r.read()


def pypi_release(pkg: str, ver: str | None = None) -> dict:
    url = f"{PYPI}/{pkg}/{ver}/json" if ver else f"{PYPI}/{pkg}/json"
    return http_json(url)


def canonicalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def index_local_wheels() -> dict[str, list[Path]]:
    idx: dict[str, list[Path]] = {}
    roots = [
        WIN_ROOT / "python310_amd64" / "environments",
        WIN_ROOT / "python312_amd64" / "environments",
        LIN_ROOT / "environments",
        WIN_ROOT / "python310_amd64_supplement",
        WIN_ROOT / "python312_amd64_supplement",
        CACHE,
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*.whl"):
            idx.setdefault(p.name, []).append(p)
    return idx


def is_any_wheel(name: str) -> bool:
    return name.lower().endswith("-none-any.whl")


def is_py_any_wheel(name: str, py: str) -> bool:
    n = name.lower()
    if not is_any_wheel(name):
        return False
    return (
        f"py{py}-none-any" in n
        or "py3-none-any" in n
        or "py2.py3-none-any" in n
    )


def is_x86_64_binary(name: str) -> bool:
    n = name.lower()
    if is_any_wheel(name):
        return False
    return any(t in n for t in ("x86_64", "amd64", "win32", "i686", "macosx"))


def is_aarch64_wheel(name: str) -> bool:
    n = name.lower()
    return "aarch64" in n and "musl" not in n


def is_armv7_wheel(name: str) -> bool:
    n = name.lower()
    return any(t in n for t in ("armv7l", "armv7", "linux_arm")) and "aarch64" not in n


def pick_wheel(files: list[dict], *, py: str, kind: str) -> dict | None:
    """kind: any | win | manylinux_x86 | aarch64 | armv7"""
    py_tag = f"cp{py}"
    scored = []
    for u in files:
        if u.get("packagetype") != "bdist_wheel":
            continue
        fn = u["filename"]
        low = fn.lower()
        if "musl" in low:
            continue
        anyw = is_py_any_wheel(fn, py)
        if kind == "any":
            if anyw:
                scored.append((0, u))
            continue
        if anyw:
            scored.append((0, u))
            continue
        if kind == "win":
            if "win_amd64" in low and py_tag in fn:
                scored.append((0, u))
        elif kind == "manylinux_x86":
            if ("x86_64" in low or "amd64" in low) and "win" not in low and py_tag in fn:
                glibc_penalty = 0 if "manylinux2014" in low or "manylinux_2_17" in low else 2
                scored.append((glibc_penalty, u))
        elif kind == "aarch64":
            if is_aarch64_wheel(fn) and py_tag in fn:
                scored.append((0 if "manylinux" in low else 1, u))
        elif kind == "armv7":
            if is_armv7_wheel(fn) and py_tag in fn:
                scored.append((0, u))
    scored.sort(key=lambda x: (x[0], -x[1].get("size", 0)))
    return scored[0][1] if scored else None


def pick_sdist(files: list[dict]) -> dict | None:
    for u in files:
        if u.get("packagetype") == "sdist":
            return u
    return None


def ensure_cached(url: str, filename: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / filename
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    data = http_bytes(url)
    tmp.write_bytes(data)
    tmp.replace(dest)
    return dest


def metadata_requires(wheel: Path) -> list[str]:
    try:
        with zipfile.ZipFile(wheel) as z:
            names = [n for n in z.namelist() if n.endswith(".dist-info/METADATA")]
            if not names:
                return []
            text = z.read(names[0]).decode("utf-8", "replace")
    except zipfile.BadZipFile:
        return []
    parsed = Parser().parsestr(text)
    reqs = []
    for k, v in parsed.items():
        if k.lower() == "requires-dist":
            if "extra ==" in v or 'extra ==' in v:
                continue
            reqs.append(v)
    return reqs


def req_name(req: str) -> str:
    return canonicalize(re.split(r"[<>=!~;( \[]", req, maxsplit=1)[0].strip())


def pip_download(dest: Path, packages: list[str], *, platform: str | None, py: str, only_binary: bool) -> tuple[int, str]:
    dest.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(PIP), "download", "-d", str(dest)]
    if platform:
        cmd += [
            "--platform", platform,
            "--python-version", py,
            "--implementation", "cp",
            "--abi", f"cp{py}",
        ]
    if only_binary:
        cmd += ["--only-binary", ":all:"]
    else:
        cmd += ["--no-deps"]
    cmd += packages
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout or "") + "\n" + (p.stderr or "")


def latest_version(pkg: str) -> str:
    return pypi_release(pkg)["info"]["version"]


def resolve_shared_versions() -> dict[str, str]:
    vers = dict(SHARED_PINS)
    for pkg in PATHOS_STACK:
        if pkg not in vers:
            vers[pkg] = latest_version(pkg)
    return vers


def place_artifact(src: Path, dest_dir: Path, reused: list[dict], downloaded: list[dict], origin: str) -> Path:
    dst = dest_dir / src.name
    link_or_copy(src, dst)
    rec = {
        "file": src.name,
        "sha256": sha256_file(src),
        "bytes": src.stat().st_size,
        "origin": origin,
        "path": str(src),
    }
    if origin.startswith("reuse:"):
        reused.append(rec)
    else:
        downloaded.append(rec)
    return dst


def fetch_pkg(pkg: str, ver: str, kind: str, py: str, local_idx: dict[str, list[Path]], dest: Path, reused, downloaded, unbuilt: list[dict]) -> Path | None:
    data = pypi_release(pkg, ver)
    files = data.get("urls") or data["releases"].get(ver, [])
    wheel = pick_wheel(files, py=py, kind=kind)
    if wheel:
        fn = wheel["filename"]
        if kind in ("aarch64", "armv7") and is_x86_64_binary(fn) and not is_any_wheel(fn):
            wheel = None
        else:
            if fn in local_idx:
                src = local_idx[fn][0]
                if kind in ("aarch64", "armv7") and is_x86_64_binary(src.name) and not is_any_wheel(src.name):
                    pass
                else:
                    return place_artifact(src, dest, reused, downloaded, f"reuse:{src}")
            src = ensure_cached(wheel["url"], fn)
            local_idx.setdefault(fn, []).append(src)
            return place_artifact(src, dest, reused, downloaded, f"pypi:{kind}")
    sdist = pick_sdist(files)
    if sdist:
        fn = sdist["filename"]
        src = ensure_cached(sdist["url"], fn)
        unbuilt.append({
            "file": fn,
            "package": pkg,
            "version": ver,
            "sha256": sha256_file(src),
            "bytes": src.stat().st_size,
            "status": "unbuilt",
            "reason": f"no compatible {kind} wheel for CPython {py}",
            "cache": str(src),
        })
        return src
    unbuilt.append({
        "file": "",
        "package": pkg,
        "version": ver,
        "sha256": "",
        "bytes": 0,
        "status": "missing",
        "reason": f"no wheel or sdist for {kind} / {py}",
    })
    return None


EXAMPLES = {
    "01_spectrum_fft.py": r'''# 傅里叶与频谱分析最小示例（NumPy / SciPy）
# 依赖：原 03 组 numpy、scipy。本补充包不重复打包这两项。
# 示例状态：未在目标机执行验证。

import numpy as np
from scipy import signal
from numpy.fft import rfft, rfftfreq

fs = 500.0
t = np.arange(0, 2, 1 / fs)
x = np.sin(2 * np.pi * 20 * t) + 0.4 * np.sin(2 * np.pi * 80 * t)

freqs = rfftfreq(x.size, 1 / fs)
spec = np.abs(rfft(x))
peak = freqs[int(np.argmax(spec[1:])) + 1]

f_welch, pxx = signal.welch(x, fs=fs, nperseg=256)
print("fft_peak_hz", round(float(peak), 3))
print("welch_peak_hz", round(float(f_welch[int(np.argmax(pxx))]), 3))
''',
    "02_wavelet_decomp_recon_denoise.py": r'''# 小波分解、重构与去噪最小示例（PyWavelets）
# 依赖：原 03 组 PyWavelets / numpy。
# 示例状态：未在目标机执行验证。

import numpy as np
import pywt

rng = np.random.default_rng(0)
t = np.linspace(0, 1, 512, endpoint=False)
clean = np.sin(2 * np.pi * 8 * t)
noisy = clean + 0.4 * rng.normal(size=t.size)

wavelet = "db4"
coeffs = pywt.wavedec(noisy, wavelet, level=4)
recon_full = pywt.waverec(coeffs, wavelet)[: noisy.size]

# 软阈值去噪：只改细节系数，近似系数保持。
thr = 0.25 * np.median(np.abs(coeffs[-1])) / 0.6745
den = [coeffs[0]]
for c in coeffs[1:]:
    den.append(pywt.threshold(c, thr, mode="soft"))
denoised = pywt.waverec(den, wavelet)[: noisy.size]

print("recon_mse", float(np.mean((recon_full - noisy) ** 2)))
print("denoise_mse_vs_clean", float(np.mean((denoised - clean) ** 2)))
print("noisy_mse_vs_clean", float(np.mean((noisy - clean) ** 2)))
''',
    "03_emd_eemd_ceemdan.py": r'''# EMD / EEMD / CEEMDAN 分解与重构（EMD-signal，导入名 PyEMD）
# pip 包名：EMD-signal ；import：from PyEMD import EMD, EEMD, CEEMDAN
# 示例状态：未在目标机执行验证。

import numpy as np
from PyEMD import CEEMDAN, EEMD, EMD

t = np.linspace(0, 1, 400, endpoint=False)
x = np.sin(2 * np.pi * 6 * t) + 0.5 * np.sin(2 * np.pi * 25 * t)

emd = EMD()
imfs = emd(x)
recon = imfs.sum(axis=0)
print("emd_imfs", imfs.shape[0], "recon_mse", float(np.mean((recon - x) ** 2)))

# trials 取得很小，仅演示调用，不作为精度基准。
eemd = EEMD(trials=8, noise_width=0.05)
e_imfs = eemd(x)
print("eemd_imfs", e_imfs.shape[0])

ceemdan = CEEMDAN(trials=8)
c_imfs = ceemdan(x)
print("ceemdan_imfs", c_imfs.shape[0], "recon_mse", float(np.mean((c_imfs.sum(axis=0) - x) ** 2)))
''',
    "04_kalman_filter_vs_smoother.py": r'''# Kalman：实时滤波 vs 使用未来观测的离线平滑
#
# filterpy：逐步 predict/update，只使用截至当前时刻的观测 → 实时 / 因果滤波。
# pykalman.smooth：RTS 平滑，使用整段未来观测 → 离线非因果，不能当实时输出。
#
# 示例状态：未在目标机执行验证。

import numpy as np
from filterpy.kalman import KalmanFilter
from pykalman import KalmanFilter as PKKalman

rng = np.random.default_rng(1)
n = 80
truth = np.cumsum(0.2 + 0.05 * rng.normal(size=n))
z = truth + 0.4 * rng.normal(size=n)

# --- 实时滤波（filterpy）---
kf = KalmanFilter(dim_x=2, dim_z=1)
kf.x = np.array([[z[0]], [0.0]])
kf.F = np.array([[1.0, 1.0], [0.0, 1.0]])
kf.H = np.array([[1.0, 0.0]])
kf.P *= 10.0
kf.R *= 0.16
kf.Q = np.array([[0.01, 0.0], [0.0, 0.01]])
online = []
for zi in z:
    kf.predict()          # 只用过去状态
    kf.update(zi)         # 只用当前观测，不用未来
    online.append(float(kf.x[0, 0]))
online = np.asarray(online)

# --- 离线平滑（pykalman RTS）---
pk = PKKalman(
    transition_matrices=[[1, 1], [0, 1]],
    observation_matrices=[[1, 0]],
    initial_state_mean=[z[0], 0],
)
filt_mean, _ = pk.filter(z)     # 因果滤波（可用实时）
smooth_mean, _ = pk.smooth(z)   # 使用 t..N 的观测，只能离线

print("online_mse", float(np.mean((online - truth) ** 2)))
print("filter_mse", float(np.mean((filt_mean[:, 0] - truth) ** 2)))
print("smooth_mse", float(np.mean((smooth_mean[:, 0] - truth) ** 2)))
print("note: smooth_mse 通常更小，因为它看到了未来观测，不能用于实时控制回路")
''',
}


DOCS_SIGNAL = r'''# 信号处理定向补充（Windows / Linux，Python 3.10 与 3.12）

本包是增量补充，**不覆盖**原 Release 资产，也不改原 `requirements_lock_en.txt`。
原 Windows 包：`wpo-full-20261030`；原 Linux 包：`lpo-full-20261030`。
Windows 上一轮工具补充仍是 `wpo-supplement-v1-20261030`，本包是另一份相关 Release。

## 覆盖范围

| 能力 | 包 | 说明 |
| --- | --- | --- |
| 傅里叶 / 频谱 | NumPy、SciPy | 已在原 **03 信号** 组，本包不重复下载 x86-64 / win_amd64 二进制 |
| 小波分解与重构 | PyWavelets | 同上，原 03 已有对应 CPython 版本的 wheel |
| EMD / EEMD / CEEMDAN | **EMD-signal** | pip 名 `EMD-signal`，**导入名 `PyEMD`** |
| Kalman 实时滤波 | filterpy | `predict` / `update`，因果 |
| Kalman 离线平滑 | pykalman | `filter` 因果；`smooth` 使用未来观测，仅离线 |

## 安装（在已有 03 环境上追加）

先按原树装好 `03_signal_*`（Windows 另可把 Linux 原 13 组里已有的 filterpy 视为无关，本包已带 Windows 可用的 any-wheel）。

Windows（PowerShell，已有 `.venv`）：

```powershell
powershell -ExecutionPolicy Bypass -File .\install_supplement_en.ps1
```

Linux：

```bash
bash ./install_supplement_en.sh
```

脚本只会安装 `requirements_supplement_en.txt` 中的**新增**包，并从 `packages_wheel/` 以及原 03（及 Linux 原 13）wheelhouse 解析依赖。

必须使用对应树的 CPython **3.10.11 / 3.12.10**，不要装进 3.14。

## 实时滤波 vs 离线平滑

- **实时 / 因果**：`filterpy.kalman.KalmanFilter.predict` + `update`，或 `pykalman.KalmanFilter.filter`。时刻 t 的输出只依赖 `z[0]..z[t]`。
- **离线平滑**：`pykalman.KalmanFilter.smooth`（RTS）。时刻 t 的输出依赖 `z[0]..z[N-1]`，含未来观测。滞后更小、误差通常更低，**不能**接到必须在采样时刻给出估计的控制回路。

## 开发板

原库开发板侧是 Raspberry Pi OS Bookworm **Python 3.11** 的 GPIO 通讯包，**不是** 3.10/3.12。
本包不为 3.11 板子补信号库，也不把 **x86-64 / win_amd64** 二进制放进板端目录。
仅当存在 **aarch64 + 对应 CPython 3.10/3.12** 的 wheel 时，才写入 `embedded_boards/aarch64/`。
armv7l 若无官方 wheel，源码与构建依赖放在 `packages_sdist_unbuilt/`，状态为 **未构建、未验证**。

## 示例是否执行验证

`examples/` 下脚本仅作最小调用示意。本轮在下载主机上**未安装、未导入、未跑通**这些示例（状态：`未执行验证`）。
'''


def write_examples(dest: Path) -> None:
    d = dest / "examples"
    d.mkdir(parents=True, exist_ok=True)
    for name, text in EXAMPLES.items():
        (d / name).write_text(text, encoding="utf-8")
    (d / "README_cn.md").write_text(
        "\n".join([
            "# 最小示例",
            "",
            "| 文件 | 内容 | 验证 |",
            "| --- | --- | --- |",
            "| `01_spectrum_fft.py` | FFT / Welch 频谱 | 未执行验证 |",
            "| `02_wavelet_decomp_recon_denoise.py` | 小波分解、重构、阈值去噪 | 未执行验证 |",
            "| `03_emd_eemd_ceemdan.py` | EMD / EEMD / CEEMDAN（`import PyEMD`） | 未执行验证 |",
            "| `04_kalman_filter_vs_smoother.py` | filterpy 实时滤波 vs pykalman 离线平滑 | 未执行验证 |",
            "",
            "在已安装原 03 + 本补充包的 venv 中运行。下载主机未执行。",
            "",
        ]),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_install_ps1(dest: Path, py: str) -> None:
    orig_env = f"03_signal_image_audio_py{py}"
    dest.joinpath("install_supplement_en.ps1").write_text(
        "\n".join([
            f"# Append signal-processing wheels onto original {orig_env} venv.",
            "# Does not modify original requirements_lock_en.txt.",
            "param(",
            '  [string]$VenvPython = "",',
            f'  [string]$OriginalWheelhouse = "..\\python{py}_amd64\\environments\\{orig_env}\\wheelhouse"',
            ")",
            '$ErrorActionPreference = "Stop"',
            "$Supp = Split-Path -Parent $MyInvocation.MyCommand.Path",
            "if (-not $VenvPython) {",
            f'  $VenvPython = Join-Path (Resolve-Path "..\\python{py}_amd64\\environments\\{orig_env}").Path ".venv\\Scripts\\python.exe"',
            "}",
            'if (-not (Test-Path $VenvPython)) { throw "venv python not found: $VenvPython" }',
            '$whl = Join-Path $Supp "packages_wheel"',
            '$lock = Join-Path $Supp "requirements_supplement_en.txt"',
            "& $VenvPython -m pip install --no-index --find-links $whl --find-links $OriginalWheelhouse -r $lock",
            'Write-Host "sdist in packages_sdist_unbuilt is NOT installed (unbuilt)."',
            "",
        ]),
        encoding="utf-8",
    )


def write_install_sh(dest: Path, py: str) -> None:
    orig_env = f"03_signal_audio_image_py{py}"
    dest.joinpath("install_supplement_en.sh").write_text(
        "\n".join([
            "#!/usr/bin/env bash",
            f"# Append signal-processing wheels onto original {orig_env} venv.",
            "set -euo pipefail",
            'SUPP="$(cd "$(dirname "$0")" && pwd)"',
            f'ORIG_WH="${{1:-$SUPP/../../environments/{orig_env}/wheelhouse}}"',
            f'STATS_WH="${{2:-$SUPP/../../environments/13_stats_timeseries_py{py}/wheelhouse}}"',
            f'VENV_PY="${{VENV_PY:-$SUPP/../../environments/{orig_env}/.venv/bin/python}}"',
            'if [ ! -x "$VENV_PY" ]; then echo "venv python not found: $VENV_PY" >&2; exit 1; fi',
            'FIND=(--find-links "$SUPP/packages_wheel")',
            'if [ -d "$ORIG_WH" ]; then FIND+=(--find-links "$ORIG_WH"); fi',
            'if [ -d "$STATS_WH" ]; then FIND+=(--find-links "$STATS_WH"); fi',
            '"$VENV_PY" -m pip install --no-index "${FIND[@]}" -r "$SUPP/requirements_supplement_en.txt"',
            'echo "sdist in packages_sdist_unbuilt is NOT installed (unbuilt)."',
            "",
        ]),
        encoding="utf-8",
    )
    dest.joinpath("install_supplement_en.sh").chmod(
        dest.joinpath("install_supplement_en.sh").stat().st_mode | stat.S_IEXEC
    )


def write_readme(dest: Path, *, os_name: str, py: str, extra: str) -> None:
    pretty = "3.10.11" if py == "310" else "3.12.10"
    dest.joinpath("README_cn.md").write_text(
        f"# {os_name} Python {pretty} 信号处理定向补充\n\n"
        + DOCS_SIGNAL
        + "\n"
        + extra
        + "\n",
        encoding="utf-8",
    )


def zip_tree(src: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for dirpath, _, filenames in os.walk(src):
            for name in filenames:
                p = Path(dirpath) / name
                arc = p.relative_to(src.parent).as_posix()
                z.write(p, arc)


def collect_supplement_pkgs(vers: dict[str, str]) -> list[tuple[str, str]]:
    names = NEW_DIRECT + PATHOS_STACK + ["scikit-base", "dill", "multiprocess"]
    out = []
    for n in names:
        out.append((n, vers[n] if n in vers else SHARED_PINS.get(n) or latest_version(n)))
    return out


def dump_unbuilt(dest: Path, rows: list[dict]) -> None:
    sdir = dest / "packages_sdist_unbuilt"
    sdir.mkdir(parents=True, exist_ok=True)
    real = [r for r in rows if r.get("status") in {"unbuilt", "missing"}]
    if real:
        note = (
            "下列条目没有与本目录目标平台/Python 版本兼容的官方 wheel，只保存源码或构建依赖。"
            "状态：**未构建、未验证**。不要把其它架构的二进制当作本目录的安装包。\n"
        )
    else:
        note = "本目录目标平台的补充项均已有兼容 wheel，无未构建源码包。\n"
    (sdir / "UNBUILT_cn.txt").write_text(note, encoding="utf-8")
    for r in real:
        src = r.get("cache")
        fn = r.get("file") or ""
        if src and fn:
            p = Path(src)
            if p.is_file():
                link_or_copy(p, sdir / fn)
    write_csv(
        dest / "UNBUILT_cn.csv",
        rows,
        ["package", "version", "file", "status", "reason", "bytes", "sha256"],
    )


def assemble_desktop(
    dest: Path,
    *,
    os_name: str,
    py: str,
    kind: str,
    local_idx: dict[str, list[Path]],
    vers: dict[str, str],
) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    whl = dest / "packages_wheel"
    sdist_dir = dest / "packages_sdist_unbuilt"
    whl.mkdir()
    sdist_dir.mkdir()
    reused: list[dict] = []
    downloaded: list[dict] = []
    unbuilt: list[dict] = []
    pkgs = collect_supplement_pkgs(vers)
    for pkg, ver in pkgs:
        art = fetch_pkg(pkg, ver, kind, py, local_idx, whl, reused, downloaded, unbuilt)
        if art and not art.name.endswith(".whl"):
            link_or_copy(art, sdist_dir / art.name)
            # remove accidentally placed sdist from wheel dir
            maybe = whl / art.name
            if maybe.exists():
                maybe.unlink()
    # If a needed any-wheel was classified unbuilt wrongly, leave as is.
    req_lines = [
        f"# New wheels only. Install on top of original 03_signal CPython {py} env.",
        "# Original lockfiles are not modified.",
        "EMD-signal==" + vers["EMD-signal"],
        "filterpy==" + vers["filterpy"],
        "pykalman==" + vers["pykalman"],
        "pathos==" + vers["pathos"],
        "pox==" + vers["pox"],
        "ppft==" + vers["ppft"],
        "dill==" + vers["dill"],
        "multiprocess==" + vers["multiprocess"],
        "scikit-base==" + vers["scikit-base"],
        "",
    ]
    dest.joinpath("requirements_supplement_en.txt").write_text("\n".join(req_lines), encoding="utf-8")
    write_csv(
        dest / "reused_from_original_cn.csv",
        reused,
        ["file", "bytes", "sha256", "origin"],
    )
    write_csv(
        dest / "downloaded_new_cn.csv",
        downloaded,
        ["file", "bytes", "sha256", "origin"],
    )
    dump_unbuilt(dest, unbuilt)
    write_examples(dest)
    extra = (
        f"目标：{'Windows 10/11 x86-64' if kind=='win' else 'Linux x86-64 glibc'}，CPython {pretty_py(py)}。\n"
        "NumPy / SciPy / PyWavelets 复用原 03 组已有兼容 wheel，见 `reused_from_original_cn.csv` 仅记录本包实际硬链接到的文件。\n"
        "本包新增主要是 EMD-signal（PyEMD）、filterpy、pykalman 及 pathos/scikit-base 等传递依赖。\n"
    )
    write_readme(dest, os_name=os_name, py=py, extra=extra)
    dest.joinpath("信号处理补充_cn.md").write_text(DOCS_SIGNAL + "\n" + extra, encoding="utf-8")
    if kind == "win":
        write_install_ps1(dest, py)
    else:
        write_install_sh(dest, py)
    dest.joinpath("VERIFICATION_cn.txt").write_text(
        "示例与安装均未在目标机执行。下载主机未 import、未跑 examples/。状态：未执行验证。\n",
        encoding="utf-8",
    )


def pretty_py(py: str) -> str:
    return "3.10.11" if py == "310" else "3.12.10"


def assemble_board_aarch64(
    dest: Path,
    py: str,
    local_idx: dict[str, list[Path]],
    vers: dict[str, str],
) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    whl = dest / "packages_wheel"
    sdist_dir = dest / "packages_sdist_unbuilt"
    whl.mkdir(exist_ok=True)
    sdist_dir.mkdir(exist_ok=True)
    reused: list[dict] = []
    downloaded: list[dict] = []
    unbuilt: list[dict] = []
    pins = dict(PINS[py])
    pins.update(vers)
    # any-wheels + aarch64 binaries. Never copy x86-64 binaries.
    names = (
        list(collect_supplement_pkgs(vers))
        + [(k, pins[k]) for k in ("numpy", "scipy", "PyWavelets", "matplotlib", "contourpy", "fonttools", "kiwisolver", "pillow", "packaging", "tqdm", "cycler", "pyparsing", "six", "python-dateutil")]
    )
    for pkg, ver in names:
        art = fetch_pkg(pkg, ver, "aarch64", py, local_idx, whl, reused, downloaded, unbuilt)
        if art is None:
            continue
        if not art.name.endswith(".whl"):
            link_or_copy(art, sdist_dir / art.name)
            maybe = whl / art.name
            if maybe.exists():
                maybe.unlink()
            continue
        if is_x86_64_binary(art.name) and not is_any_wheel(art.name):
            # refuse x86-64 in board tree
            (whl / art.name).unlink(missing_ok=True)
            unbuilt.append({
                "file": art.name,
                "package": pkg,
                "version": ver,
                "sha256": "",
                "bytes": 0,
                "status": "rejected_wrong_arch",
                "reason": "x86-64 binary not copied into board tree",
            })
    # try armv7 independently into sibling
    dest.joinpath("README_cn.md").write_text(
        f"# 开发板 aarch64 / CPython {pretty_py(py)} 信号处理补充\n\n"
        "仅含 any-wheel 与 aarch64 manylinux wheel。不含 x86-64 二进制。\n"
        "原树 Raspberry Pi Bookworm 板端是 Python 3.11，本目录供自行安装 3.10/3.12 的 aarch64 板使用。\n"
        "示例未执行验证。\n",
        encoding="utf-8",
    )
    write_csv(dest / "reused_from_original_cn.csv", reused, ["file", "bytes", "sha256", "origin"])
    write_csv(dest / "downloaded_new_cn.csv", downloaded, ["file", "bytes", "sha256", "origin"])
    dump_unbuilt(dest, unbuilt)
    req = [
        f"# aarch64 CPython {py} signal processing. Do not mix with x86-64 wheels.",
        f"numpy=={pins['numpy']}",
        f"scipy=={pins['scipy']}",
        f"PyWavelets=={pins['PyWavelets']}",
        f"matplotlib=={pins['matplotlib']}",
        f"EMD-signal=={vers['EMD-signal']}",
        f"filterpy=={vers['filterpy']}",
        f"pykalman=={vers['pykalman']}",
        f"pathos=={vers['pathos']}",
        f"scikit-base=={vers['scikit-base']}",
        "",
    ]
    dest.joinpath("requirements_supplement_en.txt").write_text("\n".join(req), encoding="utf-8")


def assemble_board_armv7(
    dest: Path,
    py: str,
    local_idx: dict[str, list[Path]],
    vers: dict[str, str],
) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    whl = dest / "packages_wheel"
    sdist_dir = dest / "packages_sdist_unbuilt"
    build_dir = dest / "build_deps_unbuilt"
    whl.mkdir(exist_ok=True)
    sdist_dir.mkdir(exist_ok=True)
    build_dir.mkdir(exist_ok=True)
    reused: list[dict] = []
    downloaded: list[dict] = []
    unbuilt: list[dict] = []
    pins = dict(PINS[py])
    pins.update(vers)
    names = list(collect_supplement_pkgs(vers)) + [
        (k, pins[k]) for k in ("numpy", "scipy", "PyWavelets", "matplotlib")
    ]
    any_ok = 0
    for pkg, ver in names:
        art = fetch_pkg(pkg, ver, "armv7", py, local_idx, whl, reused, downloaded, unbuilt)
        if art is None:
            continue
        if art.name.endswith(".whl"):
            if is_x86_64_binary(art.name) and not is_any_wheel(art.name):
                (whl / art.name).unlink(missing_ok=True)
                continue
            if is_any_wheel(art.name) or is_armv7_wheel(art.name):
                any_ok += 1
            else:
                (whl / art.name).unlink(missing_ok=True)
        else:
            link_or_copy(art, sdist_dir / art.name)
            maybe = whl / art.name
            if maybe.exists():
                maybe.unlink()
    for pkg in BUILD_FOR_SDIST:
        try:
            ver = latest_version(pkg)
        except Exception:
            continue
        art = fetch_pkg(pkg, ver, "any", py, local_idx, build_dir, reused, downloaded, unbuilt)
        if art and not art.name.endswith(".whl"):
            link_or_copy(art, build_dir / art.name)
    dest.joinpath("README_cn.md").write_text(
        f"# 开发板 armv7l / CPython {pretty_py(py)} 信号处理\n\n"
        "PyPI 通常没有 numpy/scipy/PyWavelets 的 linux_armv7l 官方 wheel。"
        "兼容的 any-wheel（EMD-signal、filterpy、pykalman、pathos）已放入 `packages_wheel/`；"
        "缺 wheel 的包以源码形式放在 `packages_sdist_unbuilt/`，构建依赖在 `build_deps_unbuilt/`。"
        "状态：**未构建、未验证**。禁止用 x86-64 wheel 代替。\n",
        encoding="utf-8",
    )
    write_csv(dest / "reused_from_original_cn.csv", reused, ["file", "bytes", "sha256", "origin"])
    write_csv(dest / "downloaded_new_cn.csv", downloaded, ["file", "bytes", "sha256", "origin"])
    dump_unbuilt(dest, unbuilt)
    dest.joinpath("requirements_supplement_sdist_en.txt").write_text(
        "\n".join([
            f"# Unbuilt source for armv7l CPython {py}. Status: unbuilt.",
            f"numpy=={pins['numpy']}",
            f"scipy=={pins['scipy']}",
            f"PyWavelets=={pins['PyWavelets']}",
            f"matplotlib=={pins['matplotlib']}",
            "",
        ]),
        encoding="utf-8",
    )


def main() -> None:
    print("indexing local wheels...", flush=True)
    local_idx = index_local_wheels()
    print("indexed", sum(len(v) for v in local_idx.values()), "paths", flush=True)
    vers = resolve_shared_versions()
    print("versions", vers, flush=True)

    win310 = WIN_ROOT / "python310_amd64_supplement_signal"
    win312 = WIN_ROOT / "python312_amd64_supplement_signal"
    lin310 = LIN_ROOT / "python310_x86_64_supplement_signal"
    lin312 = LIN_ROOT / "python312_x86_64_supplement_signal"

    assemble_desktop(win310, os_name="Windows", py="310", kind="win", local_idx=local_idx, vers=vers)
    assemble_desktop(win312, os_name="Windows", py="312", kind="win", local_idx=local_idx, vers=vers)
    assemble_desktop(lin310, os_name="Linux", py="310", kind="manylinux_x86", local_idx=local_idx, vers=vers)
    assemble_desktop(lin312, os_name="Linux", py="312", kind="manylinux_x86", local_idx=local_idx, vers=vers)

    for py, parent in (("310", lin310), ("312", lin312)):
        assemble_board_aarch64(parent / "embedded_boards" / "aarch64", py, local_idx, vers)
        assemble_board_armv7(parent / "embedded_boards" / "armv7l", py, local_idx, vers)

    dist_w = WIN_ROOT / "dist_supplement_signal"
    dist_l = LIN_ROOT / "dist_supplement_signal"
    dist_w.mkdir(exist_ok=True)
    dist_l.mkdir(exist_ok=True)
    zips = [
        (win310, dist_w / "windows_python310_amd64_supplement_signal_v1.zip"),
        (win312, dist_w / "windows_python312_amd64_supplement_signal_v1.zip"),
        (lin310, dist_l / "linux_python310_x86_64_supplement_signal_v1.zip"),
        (lin312, dist_l / "linux_python312_x86_64_supplement_signal_v1.zip"),
    ]
    for src, zp in zips:
        print("zip", zp.name, flush=True)
        zip_tree(src, zp)
        digest = sha256_file(zp)
        zp.with_suffix(zp.suffix + ".sha256").write_text(f"{digest}  {zp.name}\n", encoding="utf-8")
        print(zp.name, zp.stat().st_size, digest, flush=True)


if __name__ == "__main__":
    main()
