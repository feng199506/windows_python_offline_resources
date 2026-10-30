#!/usr/bin/env python3
"""Prepare Windows-targeted offline wheelhouses from Linux.

This script only downloads wheels and inspects metadata. It does not install
packages into the host Python, does not execute project code, and does not
claim that Windows installation has been verified.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path("/root/windows_python_offline_resources")
TOOLS = ROOT / "tools"
PIP_PYZ = TOOLS / "pip.pyz"
ENV_ROOT = ROOT / "environments"
PROJ_ROOT = ROOT / "project_specific"
STATE = ROOT / "state"
PROGRESS = ROOT / "progress_cn.csv"
ISSUES = ROOT / "compatibility_issues_cn.csv"
INVENTORY = ROOT / "package_inventory_cn.csv"

PYTHON = sys.executable

# Direct dependencies per environment. Versions are pinned only when a
# Windows-compatible combination is known and must not float to an
# incompatible latest release. Remaining packages are locked from the
# downloaded wheel set after a successful Windows-targeted resolve.
ENVIRONMENTS = [
    {
        "id": "01_base_scientific_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "基础科学计算与 Notebook",
        "purpose_cn": "科学计算、数据处理、绘图、Notebook。新项目请优先使用 Python 3.13 对应环境。",
        "framework": "numpy/scipy/pandas/jupyter",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy", "scipy", "pandas", "sympy",
            "matplotlib", "seaborn", "plotly",
            "jupyterlab", "ipykernel", "ipywidgets",
            "openpyxl", "pyarrow", "h5py", "netCDF4", "xarray",
            "pytest", "pyyaml", "requests", "httpx", "tqdm", "joblib", "psutil",
            "pywin32", "pywinpty", "colorama",
        ],
        "imports": [
            "numpy", "scipy", "pandas", "sympy", "matplotlib", "seaborn",
            "plotly", "openpyxl", "pyarrow", "h5py", "netCDF4", "xarray",
            "yaml", "requests", "httpx", "tqdm", "joblib", "psutil",
        ],
        "checks": ["numpy", "pandas"],
        "gpu": False,
    },
    {
        "id": "02_ml_stats_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "传统机器学习、统计、时间序列及 EM",
        "purpose_cn": "scikit-learn、statsmodels、梯度提升树与 hmmlearn。不含深度学习框架。",
        "framework": "scikit-learn/statsmodels/xgboost/lightgbm/catboost/hmmlearn",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy", "scipy", "pandas", "matplotlib",
            "scikit-learn", "statsmodels", "xgboost", "lightgbm", "catboost",
            "hmmlearn", "joblib", "threadpoolctl", "tqdm", "pyyaml",
            "wrapt==2.5.2",
        ],
        "imports": [
            "numpy", "scipy", "pandas", "sklearn", "statsmodels",
            "xgboost", "lightgbm", "catboost", "hmmlearn",
        ],
        "checks": ["numpy", "sklearn"],
        "gpu": False,
        "fallbacks": [
            [
                "pip", "setuptools", "wheel", "packaging",
                "numpy", "scipy", "pandas", "matplotlib",
                "scikit-learn", "statsmodels", "xgboost", "lightgbm", "catboost",
                "hmmlearn==0.3.2", "joblib", "threadpoolctl", "tqdm", "pyyaml",
                "wrapt==2.5.2",
            ],
        ],
    },
    {
        "id": "03_signal_image_audio_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "信号处理、音频及图像处理",
        "purpose_cn": "使用 opencv-python-headless，不与 opencv-python / opencv-contrib-python 混装。",
        "framework": "opencv-headless/scikit-image/librosa/mne",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy", "scipy", "pandas", "matplotlib",
            "Pillow", "opencv-python-headless==4.10.0.84", "scikit-image", "albumentations",
            "PyWavelets", "librosa", "soundfile", "mne", "wfdb",
            "imageio", "tifffile", "tqdm",
        ],
        "imports": [
            "numpy", "scipy", "PIL", "cv2", "skimage", "albumentations",
            "pywt", "librosa", "soundfile", "mne", "wfdb",
        ],
        "checks": ["numpy", "image"],
        "gpu": False,
        "fallbacks": [
            [
                "pip", "setuptools", "wheel", "packaging",
                "numpy", "scipy", "pandas", "matplotlib",
                "Pillow", "opencv-python-headless==4.11.0.86", "scikit-image", "albumentations",
                "PyWavelets", "librosa", "soundfile", "mne", "wfdb",
                "imageio", "tifffile", "tqdm",
            ],
        ],
    },
    {
        "id": "04_pytorch_cpu_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "PyTorch CPU",
        "purpose_cn": "Windows CPU 版 PyTorch。本环境不含 CUDA 包。",
        "framework": "torch/torchvision/torchaudio CPU",
        "index_url": "https://download.pytorch.org/whl/cpu",
        "extra_index": ["https://pypi.org/simple"],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy",
            "torch", "torchvision", "torchaudio",
        ],
        "imports": ["numpy", "torch", "torchvision", "torchaudio"],
        "checks": ["numpy", "torch"],
        "gpu": False,
        "source_note": "PyTorch CPU wheels from https://download.pytorch.org/whl/cpu ; other deps from PyPI.",
    },
    {
        "id": "05_gpr_bo_pytorch_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "GPR 与贝叶斯优化（PyTorch 路线）",
        "purpose_cn": "GPyTorch / BoTorch CPU。与 TensorFlow/GPflow 路线分开。",
        "framework": "gpytorch/botorch/linear_operator + torch CPU",
        "index_url": "https://download.pytorch.org/whl/cpu",
        "extra_index": ["https://pypi.org/simple"],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy", "scipy", "pandas",
            "torch",
            "linear_operator", "gpytorch", "botorch",
        ],
        "imports": ["numpy", "torch", "linear_operator", "gpytorch", "botorch"],
        "checks": ["numpy", "torch"],
        "gpu": False,
        "source_note": "torch from PyTorch CPU index; GPyTorch/BoTorch from PyPI.",
    },
    {
        "id": "06_bayesian_mc_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "贝叶斯计算与 Monte Carlo",
        "purpose_cn": "PyMC/ArviZ/emcee/cmdstanpy。CmdStan 本体需另装，不在本 wheelhouse。",
        "framework": "pymc/arviz/emcee/cmdstanpy",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy", "scipy", "pandas", "matplotlib", "xarray",
            "pymc", "arviz", "emcee", "cmdstanpy",
            "cloudpickle", "tqdm",
        ],
        "imports": ["numpy", "pymc", "arviz", "emcee", "cmdstanpy"],
        "checks": ["numpy"],
        "gpu": False,
    },
    {
        "id": "07_tensorflow_cpu_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "TensorFlow CPU / Keras",
        "purpose_cn": "Windows 原生 CPU。TF 2.11+ 无原生 Windows GPU；GPU 见 gpu_optional 与 WSL2。",
        "framework": "tensorflow-cpu 2.21 / keras",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy",
            "tensorflow-cpu==2.21.0",
            "keras",
        ],
        "imports": ["numpy", "tensorflow", "keras"],
        "checks": ["numpy", "tensorflow"],
        "gpu": False,
        "source_note": "tensorflow-cpu 2.21.0 Windows wheels from PyPI; native Windows extra package is tensorflow-intel.",
    },
    {
        "id": "08_rl_basic_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "强化学习基础",
        "purpose_cn": "Gymnasium + Stable-Baselines3 + TensorBoard。不含 Atari ROM、MuJoCo 或大规模仿真器。",
        "framework": "gymnasium/stable-baselines3/tensorboard + torch CPU",
        "index_url": "https://download.pytorch.org/whl/cpu",
        "extra_index": ["https://pypi.org/simple"],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy", "pandas", "matplotlib",
            "torch",
            "gymnasium", "pygame",
            "stable-baselines3", "tensorboard",
            "tqdm", "cloudpickle",
        ],
        "imports": ["numpy", "torch", "gymnasium", "stable_baselines3", "tensorboard"],
        "checks": ["numpy", "torch"],
        "gpu": False,
    },
    {
        "id": "09_huggingface_llm_cpu_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "Hugging Face 与大模型基础（CPU，不含权重）",
        "purpose_cn": "仅库与 tokenizer。不下载模型权重或数据集。",
        "framework": "transformers/peft/trl + torch CPU",
        "index_url": "https://download.pytorch.org/whl/cpu",
        "extra_index": ["https://pypi.org/simple"],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy",
            "torch",
            "transformers", "datasets", "tokenizers", "accelerate",
            "peft", "trl", "safetensors", "huggingface_hub", "sentencepiece",
            "protobuf", "regex", "filelock", "fsspec", "tqdm", "pyyaml",
        ],
        "imports": [
            "numpy", "torch", "transformers", "datasets", "tokenizers",
            "accelerate", "peft", "trl", "safetensors", "huggingface_hub",
            "sentencepiece",
        ],
        "checks": ["numpy", "torch"],
        "gpu": False,
    },
    {
        "id": "10_onnx_api_app_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "ONNX CPU 推理、API 与简单应用界面",
        "purpose_cn": "onnxruntime CPU，不与 onnxruntime-gpu 混装。",
        "framework": "onnx/onnxruntime/fastapi/gradio/streamlit",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy",
            "onnx", "onnxruntime",
            "fastapi", "uvicorn", "pydantic",
            "python-multipart", "starlette",
            "gradio", "streamlit",
        ],
        "imports": [
            "numpy", "onnx", "onnxruntime", "fastapi", "uvicorn",
            "pydantic", "gradio", "streamlit",
        ],
        "checks": ["numpy", "onnx"],
        "gpu": False,
    },
    {
        "id": "11_optimization_control_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "优化与控制计算",
        "purpose_cn": "CVXPY 及常见开源求解器、python-control、CasADi。",
        "framework": "cvxpy/osqp/clarabel/control/casadi",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy", "scipy",
            "cvxpy", "osqp", "clarabel", "scs",
            "control", "casadi",
        ],
        "imports": ["numpy", "scipy", "cvxpy", "osqp", "clarabel", "control", "casadi"],
        "checks": ["numpy", "cvxpy"],
        "gpu": False,
    },
    {
        "id": "07b_gpflow_tf_py310",
        "root": PROJ_ROOT,
        "py": "310",
        "title_cn": "GPflow 专用（TensorFlow 路线）",
        "purpose_cn": "与 07_tensorflow_cpu_py310 分开锁定，避免 GPflow 与最新 TF/TFP 组合不兼容。",
        "framework": "gpflow 2.11 + tensorflow-intel 2.16.2 + tfp 0.24",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy<2", "scipy",
            "tensorflow==2.16.2",
            "tensorflow-intel==2.16.2",
            "tensorflow-probability==0.24.0",
            "tf-keras==2.16.0",
            "tensorflow-io-gcs-filesystem>=0.23.1",
            "gpflow==2.11.2",
        ],
        "imports": ["numpy", "tensorflow", "tensorflow_probability", "gpflow"],
        "checks": ["numpy", "tensorflow"],
        "gpu": False,
        "optional": True,
        "fallbacks": [
            [
                "pip", "setuptools", "wheel", "packaging", "numpy", "scipy",
                "tensorflow==2.16.2",
                "tensorflow-probability==0.24.0",
                "gpflow==2.11.2",
            ],
            [
                "pip", "setuptools", "wheel", "packaging", "numpy", "scipy",
                "tensorflow-intel==2.15.1",
                "tensorflow-probability==0.23.0",
                "gpflow==2.9.2",
            ],
        ],
    },
    {
        "id": "01_base_scientific_py313",
        "root": ENV_ROOT,
        "py": "313",
        "title_cn": "基础科学计算与 Notebook（Python 3.13 新项目）",
        "purpose_cn": "仍受支持的 Python 3.13 新项目基础环境。不要与 3.10 包集合混装。",
        "framework": "numpy/scipy/pandas/jupyter on CPython 3.13",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging",
            "numpy", "scipy", "pandas", "sympy",
            "matplotlib", "seaborn", "plotly",
            "jupyterlab", "ipykernel", "ipywidgets",
            "openpyxl", "pyarrow", "h5py", "netCDF4", "xarray",
            "pytest", "pyyaml", "requests", "httpx", "tqdm", "joblib", "psutil",
            "pywin32", "pywinpty", "colorama",
        ],
        "imports": [
            "numpy", "scipy", "pandas", "sympy", "matplotlib", "seaborn",
            "plotly", "openpyxl", "pyarrow", "h5py", "netCDF4", "xarray",
        ],
        "checks": ["numpy", "pandas"],
        "gpu": False,
    },
    {
        "id": "04_pytorch_cpu_py313",
        "root": ENV_ROOT,
        "py": "313",
        "title_cn": "PyTorch CPU（Python 3.13 新项目）",
        "purpose_cn": "Python 3.13 Windows CPU 版 PyTorch。",
        "framework": "torch/torchvision/torchaudio CPU on 3.13",
        "index_url": "https://download.pytorch.org/whl/cpu",
        "extra_index": ["https://pypi.org/simple"],
        "packages": [
            "pip", "setuptools", "wheel", "packaging", "numpy",
            "torch", "torchvision", "torchaudio",
        ],
        "imports": ["numpy", "torch", "torchvision", "torchaudio"],
        "checks": ["numpy", "torch"],
        "gpu": False,
    },
    {
        "id": "07_tensorflow_cpu_py313",
        "root": ENV_ROOT,
        "py": "313",
        "title_cn": "TensorFlow CPU（Python 3.13 新项目）",
        "purpose_cn": "TF 2.21 提供 cp313 win_amd64 CPU wheel。",
        "framework": "tensorflow-cpu 2.21 on 3.13",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": [
            "pip", "setuptools", "wheel", "packaging", "numpy",
            "tensorflow-cpu==2.21.0", "keras",
        ],
        "imports": ["numpy", "tensorflow", "keras"],
        "checks": ["numpy", "tensorflow"],
        "gpu": False,
    },
]


def env_dir(spec: dict) -> Path:
    return spec["root"] / spec["id"]


def wheelhouse(spec: dict) -> Path:
    return env_dir(spec) / "wheelhouse"


def marker_path(spec: dict) -> Path:
    return env_dir(spec) / "DOWNLOAD_STATUS_en.json"


def ensure_pip_pyz() -> None:
    if PIP_PYZ.exists() and PIP_PYZ.stat().st_size > 1_000_000:
        return
    import urllib.request
    PIP_PYZ.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading portable pip.pyz")
    urllib.request.urlretrieve("https://bootstrap.pypa.io/pip/pip.pyz", PIP_PYZ)


def pip_cmd() -> list[str]:
    return [PYTHON, str(PIP_PYZ)]


def run(cmd: list[str], log_file: Path) -> subprocess.CompletedProcess:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    print("RUN", " ".join(cmd))
    with log_file.open("ab") as log:
        log.write(f"\n$ {' '.join(cmd)}\n".encode("utf-8", errors="replace"))
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=False)
        log.write(f"\n[exit {proc.returncode}]\n".encode())
    return proc


def write_requirements(spec: dict, packages: list[str]) -> Path:
    d = env_dir(spec)
    d.mkdir(parents=True, exist_ok=True)
    req = d / "requirements_direct_en.txt"
    lines = [
        f"# Direct dependencies for {spec['id']}",
        f"# Target: Windows 10/11 x86-64, CPython {spec['py'][0]}.{spec['py'][1:]}",
        "# Generated for offline wheel download. Not a historical project lockfile.",
        "",
    ]
    lines.extend(packages)
    req.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return req


def download_wheels(spec: dict, packages: list[str]) -> tuple[bool, str]:
    dest = wheelhouse(spec)
    dest.mkdir(parents=True, exist_ok=True)
    log = env_dir(spec) / "download_log_en.txt"
    req = write_requirements(spec, packages)
    cmd = pip_cmd() + [
        "download",
        "--platform", "win_amd64",
        "--python-version", spec["py"],
        "--implementation", "cp",
        "--only-binary", ":all:",
        "--dest", str(dest),
        "--index-url", spec["index_url"],
        "--disable-pip-version-check",
        "--isolated",
        "-r", str(req),
    ]
    for extra in spec.get("extra_index", []):
        cmd.extend(["--extra-index-url", extra])
    proc = run(cmd, log)
    if proc.returncode == 0:
        return True, "ok"
    tail = ""
    if log.exists():
        text = log.read_text(encoding="utf-8", errors="replace")
        tail = text[-4000:]
    return False, tail


def parse_wheel_name(name: str) -> dict:
    # PEP 427: {distribution}-{version}(-{build})?-{python}-{abi}-{platform}.whl
    stem = name[:-4] if name.endswith(".whl") else name
    parts = stem.split("-")
    if len(parts) < 5:
        return {"name": name, "distribution": stem, "version": "", "python": "", "abi": "", "platform": ""}
    platform = parts[-1]
    abi = parts[-2]
    py = parts[-3]
    if len(parts) == 6:
        dist, ver, build = parts[0], parts[1], parts[2]
        version = f"{ver}-{build}"
    else:
        dist, version = parts[0], "-".join(parts[1:-3])
    return {
        "filename": name,
        "distribution": dist,
        "version": version,
        "python": py,
        "abi": abi,
        "platform": platform,
    }


def inspect_wheel(path: Path) -> dict:
    info = parse_wheel_name(path.name)
    info["bytes"] = path.stat().st_size
    info["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    tags = []
    requires_python = ""
    requires_dist = []
    home = ""
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            wheel_name = next((n for n in names if n.endswith(".dist-info/WHEEL")), None)
            meta_name = next((n for n in names if n.endswith(".dist-info/METADATA")), None)
            if wheel_name:
                wheel_txt = zf.read(wheel_name).decode("utf-8", errors="replace")
                tags = [ln.split(":", 1)[1].strip() for ln in wheel_txt.splitlines() if ln.lower().startswith("tag:")]
            if meta_name:
                meta_txt = zf.read(meta_name).decode("utf-8", errors="replace")
                for ln in meta_txt.splitlines():
                    low = ln.lower()
                    if low.startswith("requires-python:"):
                        requires_python = ln.split(":", 1)[1].strip()
                    elif low.startswith("requires-dist:"):
                        requires_dist.append(ln.split(":", 1)[1].strip())
                    elif low.startswith("home-page:"):
                        home = ln.split(":", 1)[1].strip()
                    elif low.startswith("project-url:") and not home:
                        home = ln.split(":", 1)[1].strip()
    except zipfile.BadZipFile:
        info["readable"] = False
        info["issue"] = "bad_zip"
        return info
    info["readable"] = True
    info["tags"] = ";".join(tags)
    info["requires_python"] = requires_python
    info["requires_dist_count"] = len(requires_dist)
    info["requires_dist"] = " | ".join(requires_dist[:12])
    info["home_page"] = home
    plat = info.get("platform", "")
    py = info.get("python", "")
    abi = info.get("abi", "")
    win_ok = (
        "win_amd64" in plat
        or plat == "any"
        or plat.endswith("any")
    )
    py_ok = (
        py in {"py2.py3", "py3", "py3.py4"}
        or "py2.py3" in py
        or py.startswith("py3")
        or "abi3" in abi
        or True  # tag check below is authoritative
    )
    tag_ok = False
    for t in tags:
        tl = t.replace("-", ".")
        if "win_amd64" in t or t.endswith("none-any") or "any" == t.split("-")[-1]:
            tag_ok = True
        if "abi3" in t and "win_amd64" in t:
            tag_ok = True
    info["windows_tag_ok"] = bool(win_ok or tag_ok)
    info["py_tag"] = py
    return info


def classify_wheel_issue(info: dict, spec: dict) -> str:
    if not info.get("readable"):
        return "unreadable_wheel"
    plat = info.get("platform", "")
    if plat in {"any"} or plat.endswith("any"):
        return ""
    if "win_amd64" in plat:
        return ""
    if "linux" in plat or "manylinux" in plat or "musllinux" in plat:
        return "linux_wheel_in_windows_house"
    if "macosx" in plat:
        return "macos_wheel_in_windows_house"
    if "win32" in plat and "win_amd64" not in plat:
        return "win32_not_x64"
    return "unexpected_platform_tag"


def lockfile_from_wheels(spec: dict) -> Path:
    dest = wheelhouse(spec)
    d = env_dir(spec)
    wheels = sorted(dest.glob("*.whl"))
    lock = d / "requirements_lock_en.txt"
    lines = [
        f"# Locked from downloaded Windows wheels for {spec['id']}",
        f"# Host used pip download --platform win_amd64 --python-version {spec['py']} --implementation cp --only-binary=:all:",
        "# Do not mix with GPU or Linux wheels.",
        "",
    ]
    seen = []
    for w in wheels:
        info = parse_wheel_name(w.name)
        dist = info["distribution"].replace("_", "-")
        ver = info["version"]
        key = dist.lower()
        if key in seen:
            continue
        seen.append(key)
        lines.append(f"{dist}=={ver}")
    lock.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lock


def write_wheel_manifest(spec: dict) -> tuple[int, int, list[dict]]:
    dest = wheelhouse(spec)
    d = env_dir(spec)
    rows = []
    total = 0
    for w in sorted(dest.glob("*.whl")):
        info = inspect_wheel(w)
        info["environment"] = spec["id"]
        info["python_target"] = spec["py"]
        info["source_index"] = spec["index_url"]
        issue = classify_wheel_issue(info, spec)
        info["static_issue"] = issue
        rows.append(info)
        total += info.get("bytes", 0)
    fields = [
        "environment", "filename", "distribution", "version", "python", "abi",
        "platform", "bytes", "sha256", "tags", "requires_python",
        "requires_dist_count", "home_page", "windows_tag_ok", "static_issue",
        "source_index",
    ]
    man = d / "wheel_manifest_cn.csv"
    with man.open("w", newline="", encoding="utf-8") as f:
        wcsv = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        wcsv.writeheader()
        for row in rows:
            wcsv.writerow(row)
    src = d / "wheel_sources_en.txt"
    src.write_text(
        "\n".join(
            [
                f"environment: {spec['id']}",
                f"primary_index: {spec['index_url']}",
                f"extra_index: {', '.join(spec.get('extra_index', [])) or 'none'}",
                spec.get("source_note", ""),
                "All wheels were downloaded with pip using --only-binary=:all: and Windows tags.",
                "Filenames are official upstream names and must not be renamed.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return len(rows), total, rows


INSTALL_PS1 = r'''# Offline venv install for {env_id}
# Run in Windows PowerShell. Does not use the system site-packages.
# Does not request Administrator rights. Stops on first error.
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1
#   powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1 -PythonExe "C:\Python{py_nodot}\python.exe"

[CmdletBinding()]
param(
    [string]$PythonExe = "",
    [string]$VenvDir = ".\.venv"
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$Wheelhouse = Join-Path $Root "wheelhouse"
$Req = Join-Path $Root "requirements_lock_en.txt"

if (-not (Test-Path $Wheelhouse)) {{ throw "wheelhouse not found: $Wheelhouse" }}
if (-not (Test-Path $Req)) {{ throw "lock file not found: $Req" }}

if (-not $PythonExe) {{
    $candidates = @(
        "C:\Python{py_nodot}\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python{py_nodot}\python.exe",
        "$env:ProgramFiles\Python{py_nodot}\python.exe"
    )
    foreach ($c in $candidates) {{
        if (Test-Path $c) {{ $PythonExe = $c; break }}
    }}
}}
if (-not $PythonExe) {{
    throw "Python {py_pretty} x64 not found. Install python-{py_pretty}-amd64.exe first, then rerun with -PythonExe."
}}

$ver = & $PythonExe -c "import sys,struct; print(f'{{sys.version_info.major}}.{{sys.version_info.minor}}.{{sys.version_info.micro}} {{struct.calcsize(chr(80))*8}} {{sys.platform}}')"
Write-Host "Using interpreter: $PythonExe ($ver)"
& $PythonExe -c "import sys,struct; assert sys.version_info[:2] == ({py_major}, {py_minor}), sys.version; assert struct.calcsize(chr(80))*8 == 64; assert sys.platform == 'win32'"

if (Test-Path $VenvDir) {{
    throw "Refusing to reuse existing venv: $VenvDir. Delete it or pass -VenvDir."
}}

Write-Host "Creating venv at $VenvDir"
& $PythonExe -m venv $VenvDir
$VenvPy = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {{ throw "venv python missing: $VenvPy" }}

Write-Host "Installing from local wheelhouse (no index, no network fallback)"
& $VenvPy -m pip install --no-index --find-links $Wheelhouse --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {{ throw "Failed to install pip/setuptools/wheel from wheelhouse" }}
& $VenvPy -m pip install --no-index --find-links $Wheelhouse -r $Req
if ($LASTEXITCODE -ne 0) {{ throw "Offline install failed. Not falling back to network." }}

Write-Host "Install finished. Run: $VenvPy .\check_environment_en.py"
'''


CHECK_PY = r'''#!/usr/bin/env python3
"""Windows environment check for {env_id}. Run after offline install. Writes a local report without credentials."""
from __future__ import annotations

import importlib
import json
import platform
import struct
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_PY = ({py_major}, {py_minor})
IMPORTS = {imports}
GPU_ENV = {gpu}

def main() -> int:
    report = {{
        "environment": "{env_id}",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "executable": sys.executable,
        "python_version": sys.version,
        "version_info": list(sys.version_info),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "pointer_bits": struct.calcsize("P") * 8,
        "implementation": platform.python_implementation(),
        "ok": True,
        "errors": [],
        "imports": {{}},
        "pip_check": None,
        "ops": {{}},
        "gpu": {{}},
        "windows_install_verified": True,
        "note": "This flag is set only because this script ran on the target interpreter. Download hosts must not set it.",
    }}
    errors = report["errors"]
    if sys.version_info[:2] != EXPECTED_PY:
        errors.append(f"expected Python {{EXPECTED_PY}}, got {{sys.version_info[:2]}}")
    if struct.calcsize("P") * 8 != 64:
        errors.append("expected 64-bit interpreter")
    if sys.platform != "win32":
        errors.append(f"expected win32, got {{sys.platform}}")

    try:
        import subprocess
        pip_chk = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True, text=True, check=False,
        )
        report["pip_check"] = {{
            "returncode": pip_chk.returncode,
            "stdout": pip_chk.stdout.strip(),
            "stderr": pip_chk.stderr.strip(),
        }}
        if pip_chk.returncode != 0:
            errors.append("pip check failed")
    except Exception as exc:
        errors.append(f"pip check error: {{exc}}")

    for name in IMPORTS:
        try:
            mod = importlib.import_module(name)
            report["imports"][name] = {{
                "ok": True,
                "version": getattr(mod, "__version__", None),
            }}
        except Exception:
            report["imports"][name] = {{"ok": False, "error": traceback.format_exc()}}
            errors.append(f"import failed: {{name}}")

    if "numpy" in report["imports"] and report["imports"]["numpy"]["ok"]:
        import numpy as np
        a = np.arange(9, dtype=np.float64).reshape(3, 3)
        b = a @ a.T
        report["ops"]["numpy_matmul_sum"] = float(b.sum())

    if "pandas" in report["imports"] and report["imports"].get("pandas", {{}}).get("ok"):
        import pandas as pd
        df = pd.DataFrame({{"x": [1, 2, 3]}})
        report["ops"]["pandas_sum"] = int(df["x"].sum())

    if "torch" in report["imports"] and report["imports"].get("torch", {{}}).get("ok"):
        import torch
        t = torch.ones(2, 2)
        report["ops"]["torch_sum"] = float(t.sum().item())
        report["gpu"]["torch_cuda_is_available"] = bool(torch.cuda.is_available())
        report["gpu"]["torch_version"] = torch.__version__
        if GPU_ENV and not torch.cuda.is_available():
            errors.append("GPU environment but torch.cuda.is_available() is False")

    if "tensorflow" in report["imports"] and report["imports"].get("tensorflow", {{}}).get("ok"):
        import tensorflow as tf
        x = tf.ones((2, 2))
        report["ops"]["tf_sum"] = float(tf.reduce_sum(x).numpy())
        report["gpu"]["tf_devices"] = [d.name for d in tf.config.list_physical_devices()]

    if "onnxruntime" in report["imports"] and report["imports"].get("onnxruntime", {{}}).get("ok"):
        import onnxruntime as ort
        report["gpu"]["ort_providers"] = ort.get_available_providers()

    report["ok"] = not errors
    out = Path(__file__).with_name("check_report_en.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    txt = Path(__file__).with_name("check_report_en.txt")
    lines = [
        f"environment={{report['environment']}}",
        f"ok={{report['ok']}}",
        f"python={{report['python_version'].splitlines()[0]}}",
        f"bits={{report['pointer_bits']}}",
        f"platform={{report['platform']}}",
        f"pip_check={{report['pip_check']}}",
        f"errors={{errors}}",
    ]
    txt.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print(txt.read_text(encoding="utf-8"))
    print(f"Wrote {{out}}")
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
'''


README_CN = """# {title_cn}

- 环境编号：`{env_id}`
- 目标：Windows 10/11 x86-64，CPython {py_pretty}
- 用途：{purpose_cn}
- 框架：{framework}
- 本轮状态：**已下载并静态检查**。尚未在目标 Windows 上安装验证。

## 包含内容

- `requirements_direct_en.txt`：直接依赖（解析输入）
- `requirements_lock_en.txt`：由已下载 wheel 锁定的**完整**版本清单（含全部传递依赖）
- `wheelhouse/`：目标包及其全部传递依赖的 Windows wheel，文件名为上游原始名称。离线安装时用 `--no-index --find-links wheelhouse -r requirements_lock_en.txt`，不要只装 direct 文件。
- `wheel_manifest_cn.csv`：包名、版本、标签、大小、SHA256、依赖摘要
- `install_offline_en.ps1`：离线创建 venv 并安装
- `check_environment_en.py`：在 Windows 安装后运行

## 限制

- 这是通用科研基础环境，不是某个历史项目的精确复现。
- 不能与其他 Python 版本、GPU 包或 WSL2/Linux wheel 混装。
- Python 包安装完成不等于权重、数据、编译器或外部服务已具备。
- {source_note}

## Windows 安装步骤

1. 安装本套件中的 `python-{installer}-amd64.exe`（独立树用 `runtime/`，库根用 `installers/`）。
2. 安装同位置的 `vc_redist.x64.exe`（多数二进制扩展需要）。
3. 在本目录打开 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\\install_offline_en.ps1 -PythonExe "C:\\Python{py_nodot}\\python.exe"
.\\ .venv\\Scripts\\python.exe .\\check_environment_en.py
```

4. 只有 `check_report_en.json` 中 `ok: true` 且本机实际运行后，才可把该环境记为“安装验证通过”。
"""


def write_scripts(spec: dict) -> None:
    d = env_dir(spec)
    py = spec["py"]
    py_major = int(py[:1]) if len(py) == 3 else int(py[:2])  # 310 -> handled below
    py_major, py_minor = int(py[:-2] or "3"), int(py[-2:])
    # 310 -> 3, 10; 313 -> 3, 13
    py_major = 3
    py_minor = int(py[1:])
    py_pretty = f"{py_major}.{py_minor}"
    py_nodot = f"{py_major}{py_minor}"
    installer = {"310": "3.10.11", "312": "3.12.10", "313": "3.13.17"}.get(py, f"3.{py_minor}")
    ps1 = INSTALL_PS1.format(
        env_id=spec["id"],
        py_nodot=py_nodot,
        py_pretty=py_pretty,
        py_major=py_major,
        py_minor=py_minor,
    )
    (d / "install_offline_en.ps1").write_text(ps1, encoding="utf-8")
    check = CHECK_PY.format(
        env_id=spec["id"],
        py_major=py_major,
        py_minor=py_minor,
        imports=repr(spec["imports"]),
        gpu=repr(bool(spec.get("gpu"))),
    )
    (d / "check_environment_en.py").write_text(check, encoding="utf-8")
    readme = README_CN.format(
        title_cn=spec["title_cn"],
        env_id=spec["id"],
        py_pretty=py_pretty,
        purpose_cn=spec["purpose_cn"],
        framework=spec["framework"],
        source_note=spec.get("source_note", "包来自 PyPI 或框架官方索引。"),
        installer=installer,
        py_nodot=py_nodot,
    )
    (d / "README_cn.md").write_text(readme, encoding="utf-8")


def append_progress(row: dict) -> None:
    fields = [
        "environment", "status", "python", "direct_packages", "wheel_count",
        "total_bytes", "started_utc", "finished_utc", "notes",
    ]
    new_file = not PROGRESS.exists()
    with PROGRESS.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def append_issue(row: dict) -> None:
    fields = [
        "environment", "item", "issue_type", "detail", "workaround", "blocks_offline_windows",
    ]
    new_file = not ISSUES.exists()
    with ISSUES.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def prepare_one(spec: dict) -> dict:
    d = env_dir(spec)
    d.mkdir(parents=True, exist_ok=True)
    mark = marker_path(spec)
    if mark.exists():
        prev = json.loads(mark.read_text(encoding="utf-8"))
        if prev.get("status") == "downloaded":
            print(f"SKIP {spec['id']} (already downloaded)")
            write_scripts(spec)
            n, total, rows = write_wheel_manifest(spec)
            lockfile_from_wheels(spec)
            return {
                "environment": spec["id"],
                "status": "downloaded",
                "python": spec["py"],
                "direct_packages": " ".join(spec["packages"]),
                "wheel_count": n,
                "total_bytes": total,
                "started_utc": prev.get("started_utc", ""),
                "finished_utc": prev.get("finished_utc", ""),
                "notes": "resumed, already complete",
                "rows": rows,
            }
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_scripts(spec)
    attempts = [spec["packages"]] + list(spec.get("fallbacks") or [])
    ok = False
    detail = ""
    used = attempts[0]
    for i, pkgs in enumerate(attempts):
        print(f"=== {spec['id']} attempt {i+1}/{len(attempts)} ===")
        # Clean incomplete wheelhouse only on retry after failure
        if i > 0 and wheelhouse(spec).exists():
            shutil.rmtree(wheelhouse(spec), ignore_errors=True)
        ok, detail = download_wheels(spec, pkgs)
        used = pkgs
        if ok:
            break
        append_issue({
            "environment": spec["id"],
            "item": " ".join(pkgs),
            "issue_type": "resolve_or_download_failed",
            "detail": detail[-1500:],
            "workaround": "see fallbacks or compatibility_issues_cn.csv",
            "blocks_offline_windows": "yes" if i == len(attempts) - 1 else "retrying",
        })
    n, total, rows = (0, 0, [])
    status = "failed"
    if ok:
        lockfile_from_wheels(spec)
        n, total, rows = write_wheel_manifest(spec)
        bad = [r for r in rows if r.get("static_issue")]
        sdist_like = list((wheelhouse(spec)).glob("*.tar.gz")) + list((wheelhouse(spec)).glob("*.zip"))
        if sdist_like:
            append_issue({
                "environment": spec["id"],
                "item": ",".join(p.name for p in sdist_like),
                "issue_type": "non_wheel_artifact",
                "detail": "Source distributions were downloaded despite --only-binary=:all:",
                "workaround": "remove and treat as unavailable Windows wheel",
                "blocks_offline_windows": "yes",
            })
        for b in bad:
            append_issue({
                "environment": spec["id"],
                "item": b.get("filename", ""),
                "issue_type": b.get("static_issue", ""),
                "detail": f"platform={b.get('platform')} python={b.get('python')} abi={b.get('abi')}",
                "workaround": "do not install this file on Windows x64",
                "blocks_offline_windows": "yes",
            })
        status = "downloaded"
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    result = {
        "environment": spec["id"],
        "status": status,
        "python": spec["py"],
        "direct_packages": " ".join(used),
        "wheel_count": n,
        "total_bytes": total,
        "started_utc": started,
        "finished_utc": finished,
        "notes": "static download only; Windows install not verified",
        "rows": rows,
        "error_tail": "" if ok else detail[-2000:],
    }
    mark.write_text(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2), encoding="utf-8")
    append_progress({k: v for k, v in result.items() if k not in {"rows", "error_tail"}})
    return result


def main() -> int:
    ensure_pip_pyz()
    STATE.mkdir(parents=True, exist_ok=True)
    ENV_ROOT.mkdir(parents=True, exist_ok=True)
    PROJ_ROOT.mkdir(parents=True, exist_ok=True)
    all_rows = []
    results = []
    start_from = os.environ.get("START_FROM", "")
    started = not start_from
    for spec in ENVIRONMENTS:
        if not started:
            if spec["id"] == start_from:
                started = True
            else:
                print(f"WAIT {spec['id']}")
                continue
        res = prepare_one(spec)
        results.append(res)
        all_rows.extend(res.get("rows") or [])
        (STATE / "last_result.json").write_text(json.dumps(
            {k: v for k, v in res.items() if k != "rows"}, indent=2
        ), encoding="utf-8")
    fields = [
        "environment", "filename", "distribution", "version", "python", "abi",
        "platform", "bytes", "sha256", "tags", "requires_python",
        "windows_tag_ok", "static_issue", "source_index",
    ]
    with INVENTORY.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in all_rows:
            w.writerow(row)
    summary = []
    for r in results:
        summary.append(
            f"{r['environment']}: {r['status']} wheels={r['wheel_count']} bytes={r['total_bytes']}"
        )
        if r.get("error_tail"):
            summary.append(r["error_tail"][:500])
    (STATE / "summary_en.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))
    return 0 if all(r["status"] == "downloaded" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
