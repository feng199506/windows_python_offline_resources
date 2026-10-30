#!/usr/bin/env python3
"""Assemble Windows 3.10/3.12 supplement trees. Does not modify original lockfiles."""
from __future__ import annotations

import csv
import hashlib
import os
import shutil
import stat
import zipfile
from pathlib import Path

ROOT = Path("/root/windows_python_offline_resources")
CACHE = ROOT / "supplement_cache"
DOCS = ROOT / "supplement_docs"
OUT310 = ROOT / "python310_amd64_supplement"
OUT312 = ROOT / "python312_amd64_supplement"
DIST = ROOT / "dist_supplement"

ENV_BLURB = {
    "01_base_scientific": (
        "数据处理、统计摘要、绘图和 Jupyter Notebook。适合作为多数分析任务的起点。",
        [
            ("numpy", "多维数组", "https://numpy.org/doc/stable/"),
            ("pandas", "表格", "https://pandas.pydata.org/docs/"),
            ("scipy", "科学计算", "https://docs.scipy.org/doc/scipy/"),
            ("matplotlib", "绘图", "https://matplotlib.org/stable/"),
            ("jupyterlab", "Notebook", "https://jupyterlab.readthedocs.io/"),
        ],
        "无额外外部程序。读远程 URL 才需要联网。",
    ),
    "02_ml_stats": (
        "sklearn 流水线、统计模型、提升树和 HMM，不含深度学习。",
        [
            ("scikit-learn", "经典 ML", "https://scikit-learn.org/stable/"),
            ("xgboost", "提升树（本库锁 2.0.3）", "https://xgboost.readthedocs.io/"),
            ("statsmodels", "统计与时序", "https://www.statsmodels.org/"),
        ],
        "catboost 出图需要系统 Graphviz，本轮补充包未收录 Graphviz。",
    ),
    "03_signal_image_audio": (
        "OpenCV headless、scikit-image、librosa、MNE 等图像音频信号。",
        [
            ("opencv-python-headless", "图像（仅 headless 4.10）", "https://docs.opencv.org/"),
            ("librosa", "音频", "https://librosa.org/doc/latest/"),
            ("mne", "脑电/生理信号", "https://mne.tools/stable/"),
        ],
        "不要与 opencv-python 混装。命令行 FFmpeg 见补充包 19 用途。",
    ),
    "04_pytorch_cpu": (
        "PyTorch CPU 训练/推理小规模任务。",
        [
            ("torch", "张量与模块（CPU 索引）", "https://pytorch.org/docs/stable/"),
        ],
        "无 CUDA。权重未下载。",
    ),
    "05_gpr_bo_pytorch": (
        "GPyTorch / BoTorch 高斯过程与贝叶斯优化（PyTorch CPU）。",
        [
            ("gpytorch", "GPR", "https://docs.gpytorch.ai/"),
            ("botorch", "贝叶斯优化", "https://botorch.org/docs/introduction"),
        ],
        "与 07b GPflow 路线分开。",
    ),
    "06_bayesian_mc": (
        "PyMC、ArviZ、emcee、cmdstanpy。Stan 编译器本体未打包。",
        [
            ("pymc", "贝叶斯模型", "https://www.pymc.io/"),
            ("cmdstanpy", "Stan Python 封装", "https://mc-stan.org/cmdstanpy/"),
        ],
        "CmdStan 可执行工具链仍缺失。",
    ),
    "07_tensorflow_cpu": (
        "TensorFlow CPU 2.21 与 Keras。",
        [
            ("tensorflow-cpu", "TF CPU", "https://www.tensorflow.org/install"),
            ("keras", "高层 API", "https://keras.io/"),
        ],
        "无原生 Windows GPU。不要与 07b 混装。",
    ),
    "07b_gpflow_tf": (
        "GPflow，锁定 TF-intel 2.16.2 与 numpy<2。",
        [
            ("gpflow", "TF 路线 GPR", "https://gpflow.github.io/GPflow/"),
        ],
        "独立环境。",
    ),
    "08_rl_basic": (
        "Gymnasium 经典控制 + Stable-Baselines3。",
        [
            ("gymnasium", "RL API", "https://gymnasium.farama.org/"),
            ("stable-baselines3", "基线算法", "https://stable-baselines3.readthedocs.io/"),
        ],
        "无 MuJoCo、无 Atari ROM。",
    ),
    "09_huggingface_llm_cpu": (
        "transformers 等库与 tokenizer，不含权重。",
        [
            ("transformers", "模型库（无权重）", "https://huggingface.co/docs/transformers"),
        ],
        "from_pretrained 默认联网。",
    ),
    "10_onnx_api_app": (
        "ONNX Runtime CPU、FastAPI、Gradio、Streamlit。",
        [
            ("onnxruntime", "CPU 推理", "https://onnxruntime.ai/"),
            ("fastapi", "HTTP API", "https://fastapi.tiangolo.com/"),
        ],
        "勿混装 onnxruntime-gpu。",
    ),
    "11_optimization_control": (
        "CVXPY、开源求解器、CasADi、python-control。",
        [
            ("cvxpy", "凸优化", "https://www.cvxpy.org/"),
            ("casadi", "最优控制/符号", "https://web.casadi.org/"),
        ],
        "无 Gurobi/MOSEK。",
    ),
    "12_scientific_extra": (
        "Numba、Dask、Polars、地理空间等科学扩展。",
        [
            ("numba", "JIT", "https://numba.readthedocs.io/"),
            ("polars", "DataFrame", "https://docs.pola.rs/"),
            ("geopandas", "地理表", "https://geopandas.org/"),
        ],
        "与 01 的 Notebook 全集分开。",
    ),
    "13_stats_optimize_extra": (
        "生存分析、计量、超参搜索、cvxopt。",
        [
            ("optuna", "超参", "https://optuna.org/"),
            ("lifelines", "生存分析", "https://lifelines.readthedocs.io/"),
        ],
        "与 11 的 CVXPY 分开。",
    ),
    "14_ml_extra": (
        "不平衡学习、SHAP、UMAP、HDBSCAN。lime 仅补充源码。",
        [
            ("shap", "解释", "https://shap.readthedocs.io/"),
            ("lime", "局部解释（sdist 未构建）", "https://lime-ml.readthedocs.io/"),
        ],
        "lime 还需要 03 组的 scikit-image。",
    ),
    "15_dl_pytorch_extra": (
        "Lightning、timm、kornia（CPU）。",
        [
            ("lightning", "训练循环", "https://lightning.ai/docs/pytorch/stable/"),
            ("timm", "视觉模型库", "https://huggingface.co/docs/timm"),
        ],
        "预训练权重未下载。",
    ),
    "16_timeseries_quant": (
        "时序模型、行情接口、回测。ta 源码待构建；3.10 的 akshare 在补充包。",
        [
            ("yfinance", "行情（联网）", "https://github.com/ranaroussi/yfinance"),
            ("akshare", "财经数据（联网）", "https://akshare.akfamily.xyz/"),
            ("ta", "指标（sdist 未构建）", "https://technical-analysis-library-in-python.readthedocs.io/"),
        ],
        "接口类包默认要联网。",
    ),
    "17_nlp_classic": (
        "NLTK/spaCy/Gensim。jieba 源码待构建。模型与语料未下。",
        [
            ("spacy", "NLP 管道", "https://spacy.io/usage"),
            ("jieba", "中文分词（sdist 未构建）", "https://github.com/fxsjy/jieba"),
        ],
        "nltk.download / spaCy 模型离线不可用。",
    ),
    "17b_nlp_sentence_transformers": (
        "句向量库，不含权重，与 17 分开以免混装 torch。",
        [
            ("sentence-transformers", "句嵌入", "https://sbert.net/"),
        ],
        "加载模型默认联网。",
    ),
    "18_vision_extra": (
        "OCR 封装、哈希、RAW。Tesseract 引擎在补充包。",
        [
            ("pytesseract", "OCR 封装", "https://pypi.org/project/pytesseract/"),
        ],
        "必须安装 Tesseract 并配置 tessdata。",
    ),
    "19_av_extra": (
        "PyAV/MoviePy/pydub。FFmpeg 可执行文件在补充包。",
        [
            ("av", "PyAV", "https://pyav.org/docs/stable/"),
            ("moviepy", "剪辑封装", "https://zulko.github.io/moviepy/"),
        ],
        "转码需要 FFmpeg。",
    ),
    "20_web_api_extra": (
        "Flask/Django/Celery。Redis 服务器未打包。",
        [
            ("flask", "Web", "https://flask.palletsprojects.com/"),
            ("django", "Web", "https://docs.djangoproject.com/"),
        ],
        "不含 gunicorn。",
    ),
    "21_database": (
        "SQLAlchemy、驱动、DuckDB。数据库服务器未打包。",
        [
            ("sqlalchemy", "ORM/SQL", "https://docs.sqlalchemy.org/"),
            ("duckdb", "嵌入式分析库", "https://duckdb.org/docs/"),
        ],
        "连接远程库需要网络与服务器。",
    ),
    "22_crawler": (
        "Scrapy 与 Selenium。浏览器与驱动在补充包。",
        [
            ("scrapy", "爬虫", "https://docs.scrapy.org/"),
            ("selenium", "浏览器驱动", "https://www.selenium.dev/documentation/"),
        ],
        "抓取网站需要联网。",
    ),
    "22b_playwright": (
        "Playwright Python。Firefox/WebKit zip 已下；官方 Chromium 改用 Chrome for Testing。",
        [
            ("playwright", "浏览器自动化", "https://playwright.dev/python/"),
        ],
        "playwright==1.64.1。访问站点需联网。",
    ),
    "23_office_pdf": (
        "docx/pptx/xlsx/PDF。odfpy 源码待构建。",
        [
            ("python-docx", "Word", "https://python-docx.readthedocs.io/"),
            ("pypdf", "PDF", "https://pypdf.readthedocs.io/"),
            ("odfpy", "ODF（sdist 未构建）", "https://github.com/eea/odfpy"),
        ],
        "无 WeasyPrint/GTK、无 Java/tabula。",
    ),
    "24_gui_tk": (
        "Tk 路线桌面 UI。",
        [
            ("customtkinter", "Tk 美化", "https://customtkinter.tomschimansky.com/"),
        ],
        "不要与 Qt/wx 混装。",
    ),
    "24b_gui_pyqt6": (
        "PyQt6 桌面 UI。",
        [("PyQt6", "Qt 绑定", "https://www.riverbankcomputing.com/static/Docs/PyQt6/")],
        "不要与 PySide6 混装。",
    ),
    "24c_gui_pyside6": (
        "PySide6 桌面 UI。",
        [("PySide6", "Qt for Python", "https://doc.qt.io/qtforpython-6/")],
        "不要与 PyQt6 混装。",
    ),
    "24d_gui_wx": (
        "wxPython 桌面 UI。",
        [("wxPython", "wx", "https://docs.wxpython.org/")],
        "独立环境。",
    ),
    "25_devtools": (
        "pytest、ruff、mypy、sphinx、pyinstaller 等。",
        [
            ("pytest", "测试", "https://docs.pytest.org/"),
            ("ruff", "检查/格式", "https://docs.astral.sh/ruff/"),
            ("pyinstaller", "打包", "https://pyinstaller.org/"),
        ],
        "无嵌入式烧录工具。",
    ),
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def env_key(name: str) -> str:
    return name.replace("_py310", "").replace("_py312", "")


def append_env_readme(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(".\\ .venv\\Scripts\\python.exe", ".\\.venv\\Scripts\\python.exe")
    key = env_key(path.parent.name)
    if key not in ENV_BLURB:
        path.write_text(text, encoding="utf-8")
        return
    if "## 本组能做什么" in text:
        path.write_text(text, encoding="utf-8")
        return
    can, pkgs, extra = ENV_BLURB[key]
    lines = [
        "",
        "## 本组能做什么",
        "",
        can,
        "",
        extra,
        "",
        "## 常用目标包",
        "",
        "| 包 | 作用 | 官方文档 |",
        "| --- | --- | --- |",
    ]
    for name, role, url in pkgs:
        lines.append(f"| `{name}` | {role} | {url} |")
    lines += [
        "",
        "其余条目是传递依赖，见 `requirements_lock_en.txt`，不逐个说明。",
        "必须使用本树 `runtime` 中的 Python 3.10 或 3.12，不能装进 3.14。",
        "外部工具与未构建源码见同级目录的 `python3xx_amd64_supplement/`。",
        "",
    ]
    path.write_text(text.rstrip() + "\n" + "\n".join(lines), encoding="utf-8")


def update_tree_readme(tree: Path, py: str, supp_name: str) -> None:
    p = tree / "README_cn.md"
    text = p.read_text(encoding="utf-8")
    marker = "## 本轮定向补充"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n"
    add = f"""
{marker}

原锁定清单未改。新增内容在独立目录 `{supp_name}/`（随补充 zip 发布，原 Release tar 不变）。

| 类别 | 内容 |
| --- | --- |
| 已下载 wheel | 原 31 组 wheelhouse；3.10 另补 `akshare==1.18.88` 及部分依赖 wheel |
| 源码待构建 | lime 0.2.0.1、ta 0.11.0、jieba 0.42.1、odfpy 1.4.1、jsonpath 0.82.2（**未构建、未验证**，不是 Linux wheel） |
| 已下载外部工具 | Chrome for Testing 156.0.8078.4、chromedriver、headless-shell、geckodriver 0.37.1、msedgedriver 156.0.4314.50、Playwright Firefox/WebKit/ffmpeg、FFmpeg 9.0.2 essentials、Tesseract 5.4.0 与 eng/chi_sim/chi_tra/osd |
| 仍缺失 | Playwright 官方 Chromium rev 1248 zip、完整 Firefox 安装包、CmdStan 工具链、CUDA、HF/spaCy/NLTK 数据、串口/烧录工具、数据库服务器 |

必须用 `runtime/python-{py}-amd64.exe` 创建 venv，**不支持直接装入 Python 3.14**。
说明：`{supp_name}/离线安装与使用_cn.md`。
"""
    p.write_text(text.rstrip() + "\n" + add, encoding="utf-8")


def write_supplement_readme(dest: Path, py: str, tag: str) -> None:
    pretty = "3.10.11" if py == "310" else "3.12.10"
    dest.joinpath("README_cn.md").write_text(
        f"""# Python {pretty} 定向补充包 v1

适用原 Release 标签：**`{tag}`**  
https://github.com/feng199506/windows_python_offline_resources/releases/tag/{tag}

## 解压位置

与原 tar **解压到同一目录**（例如 `D:\\wpo\\`），得到与 `python{py}_amd64\\` 并列的 `python{py}_amd64_supplement\\`。  
不要覆盖原树中的 `requirements_lock_en.txt` 和 wheelhouse。

## 使用方法

见 `离线安装与使用_cn.md`。索引见 `常用工具与包用途索引_cn.md`。任务示例见 `常见任务快速入门_cn.md`。

必须使用 `python{py}_amd64\\runtime\\python-{pretty}-amd64.exe`，不能装进 Python 3.14。

## 本包内容摘要

- `packages_sdist/`：lime、ta、jieba、odfpy、jsonpath 源码。**未构建、未验证。**
- `packages_wheel/`：仅本轮新增、可用于 Windows 的 wheel（3.10 含 akshare 1.18.88 等）。3.12 的 akshare 已在原 lock。
- `external/`：浏览器、驱动、FFmpeg、Tesseract 与语言数据。
- 原 lock 不变；新项见 `requirements_supplement_en.txt` 与 `requirements_supplement_sdist_en.txt`。
""",
        encoding="utf-8",
    )


def write_ps1(dest: Path, py: str) -> None:
    exe = "C:\\Python310\\python.exe" if py == "310" else "C:\\Python312\\python.exe"
    dest.joinpath("install_supplement_en.ps1").write_text(
        rf'''# Append supplement wheels onto an existing venv of this Python version.
# Does not modify original requirements_lock_en.txt.
# Usage (from an environment directory that already has .venv):
#   powershell -ExecutionPolicy Bypass -File ..\..\python{py}_amd64_supplement\install_supplement_en.ps1
param(
  [string]$PythonExe = "{exe}",
  [string]$VenvPython = ""
)
$ErrorActionPreference = "Stop"
$Supp = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $VenvPython) {{
  $VenvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
}}
if (-not (Test-Path $VenvPython)) {{
  throw "venv python not found: $VenvPython ; create the original env first with install_offline_en.ps1"
}}
$whl = Join-Path $Supp "packages_wheel"
$lock = Join-Path $Supp "requirements_supplement_en.txt"
if (Test-Path $lock) {{
  & $VenvPython -m pip install --no-index --find-links $whl -r $lock
}}
Write-Host "sdist packages are NOT installed by this script (unbuilt). See requirements_supplement_sdist_en.txt"
''',
        encoding="utf-8",
    )


def copy_externals(dest: Path) -> list[dict]:
    rows = []
    mapping = [
        (CACHE / "ffmpeg" / "ffmpeg-9.0.2-essentials_build.zip", dest / "external" / "ffmpeg" / "ffmpeg-9.0.2-essentials_build.zip",
         "FFmpeg 9.0.2 essentials", "gyan.dev / GitHub GyanD/codexffmpeg", "19_av_extra; 命令行转码",
         "解压后把 bin\\ 加入 PATH"),
        (CACHE / "tesseract" / "tesseract-ocr-w64-setup-5.4.0.20240606.exe", dest / "external" / "tesseract" / "tesseract-ocr-w64-setup-5.4.0.20240606.exe",
         "Tesseract OCR 5.4.0", "UB Mannheim", "18_vision_extra / pytesseract",
         "运行安装程序；TESSDATA_PREFIX 指向 tessdata"),
        (CACHE / "chrome" / "chrome-win64.zip", dest / "external" / "chrome" / "chrome-win64.zip",
         "Chrome for Testing 156.0.8078.4", "Chrome for Testing", "22_crawler; 22b_playwright Chromium 替代",
         "解压后 chrome.exe；Playwright 用 executable_path"),
        (CACHE / "chrome" / "VERSION.txt", dest / "external" / "chrome" / "VERSION.txt",
         "Chrome version pin", "Chrome for Testing", "22 / 22b", ""),
        (CACHE / "chrome_headless_shell" / "chrome-headless-shell-win64.zip", dest / "external" / "chrome_headless_shell" / "chrome-headless-shell-win64.zip",
         "Chrome headless shell 156.0.8078.4", "Chrome for Testing", "22 无头", "解压使用"),
        (CACHE / "chromedriver" / "chromedriver-win64.zip", dest / "external" / "chromedriver" / "chromedriver-win64.zip",
         "ChromeDriver 156.0.8078.4", "Chrome for Testing", "22_crawler Selenium", "与 Chrome for Testing 同版本"),
        (CACHE / "geckodriver" / "geckodriver-v0.37.1-win64.zip", dest / "external" / "geckodriver" / "geckodriver-v0.37.1-win64.zip",
         "geckodriver 0.37.1", "Mozilla GitHub", "22_crawler Firefox", "需本机已装 Firefox；完整 Firefox 安装包未收录"),
        (CACHE / "msedgedriver" / "edgedriver_win64.zip", dest / "external" / "msedgedriver" / "edgedriver_win64.zip",
         "msedgedriver 156.0.4314.50", "Microsoft", "22_crawler 系统 Edge", "Windows 自带 Edge"),
        (CACHE / "msedgedriver" / "VERSION.txt", dest / "external" / "msedgedriver" / "VERSION.txt",
         "EdgeDriver version pin", "Microsoft", "22", ""),
        (CACHE / "playwright" / "firefox-win64.zip", dest / "external" / "playwright" / "firefox-win64.zip",
         "Playwright Firefox rev 1555", "playwright.azureedge.net", "22b playwright 1.64.1", "解压到 PLAYWRIGHT_BROWSERS_PATH"),
        (CACHE / "playwright" / "webkit-win64.zip", dest / "external" / "playwright" / "webkit-win64.zip",
         "Playwright WebKit rev 2370", "playwright.azureedge.net", "22b", "同上"),
        (CACHE / "playwright" / "ffmpeg-win64.zip", dest / "external" / "playwright" / "ffmpeg-win64.zip",
         "Playwright ffmpeg rev 1013", "playwright.azureedge.net", "22b 媒体", "Playwright 内部用，不是 gyan FFmpeg"),
        (CACHE / "playwright" / "NOTES.txt", dest / "external" / "playwright" / "NOTES.txt",
         "Playwright CDN 缺口说明", "本轮记录", "22b", "chromium-win64 rev 1248 不可用"),
    ]
    for lang in ("eng", "chi_sim", "chi_tra", "osd"):
        mapping.append(
            (
                CACHE / "tessdata" / f"{lang}.traineddata",
                dest / "external" / "tessdata" / f"{lang}.traineddata",
                f"Tesseract tessdata {lang}",
                "github.com/tesseract-ocr/tessdata",
                "18_vision_extra",
                "TESSDATA_PREFIX 或拷入安装目录 tessdata",
            )
        )
    for src, dst, title, source, envs, how in mapping:
        if not src.exists():
            raise FileNotFoundError(src)
        link_or_copy(src, dst)
        rows.append({
            "file": str(dst.relative_to(dest)).replace("\\", "/"),
            "title": title,
            "source": source,
            "environments": envs,
            "how": how,
            "bytes": dst.stat().st_size,
            "sha256": sha256_file(dst),
            "kind": "external",
            "status": "downloaded_not_windows_verified",
        })
    return rows


def copy_python_artifacts(dest: Path, py: str) -> list[dict]:
    rows = []
    sdist_names = [
        "lime-0.2.0.1.tar.gz",
        "ta-0.11.0.tar.gz",
        "jieba-0.42.1.tar.gz",
        "odfpy-1.4.1.tar.gz",
        "jsonpath-0.82.2.tar.gz",
    ]
    for name in sdist_names:
        src = CACHE / "sdist" / name
        dst = dest / "packages_sdist" / name
        link_or_copy(src, dst)
        rows.append({
            "file": str(dst.relative_to(dest)).replace("\\", "/"),
            "title": name,
            "source": "PyPI sdist",
            "environments": "14/16/17/23 as applicable",
            "how": "pip install from sdist on Windows; NOT built here",
            "bytes": dst.stat().st_size,
            "sha256": sha256_file(dst),
            "kind": "sdist_unbuilt",
            "status": "source_only_not_built_not_verified",
        })
    if py == "310":
        # new wheels not in original 16 lock
        want = [
            "akshare-1.18.88-py3-none-any.whl",
            "html5lib-1.1-py2.py3-none-any.whl",
            "tabulate-0.10.0-py3-none-any.whl",
            "decorator-5.3.1-py3-none-any.whl",
            "mini_racer-0.14.1-py3-none-win_amd64.whl",
            "webencodings-0.6.1-py3-none-any.whl",
            "xlrd-2.0.2-py2.py3-none-any.whl",
            "openpyxl-3.1.5-py2.py3-none-any.whl",
            "et_xmlfile-2.0.0-py3-none-any.whl",
        ]
        for name in want:
            src = CACHE / "akshare310_deps" / name
            if not src.exists():
                src = CACHE / "akshare310" / name
            dst = dest / "packages_wheel" / name
            link_or_copy(src, dst)
            rows.append({
                "file": str(dst.relative_to(dest)).replace("\\", "/"),
                "title": name,
                "source": "PyPI",
                "environments": "16_timeseries_quant_py310",
                "how": "pip install --no-index after original 16 lock",
                "bytes": dst.stat().st_size,
                "sha256": sha256_file(dst),
                "kind": "windows_or_any_wheel",
                "status": "downloaded_not_windows_verified",
            })
        dest.joinpath("requirements_supplement_en.txt").write_text(
            "\n".join([
                "# Additional installable wheels for python310. Do not merge into original lock.",
                "# Install inside 16_timeseries_quant_py310 venv after original lock.",
                "akshare==1.18.88",
                "html5lib==1.1",
                "tabulate==0.10.0",
                "decorator==5.3.1",
                "mini-racer==0.14.1",
                "webencodings==0.6.1",
                "xlrd==2.0.2",
                "openpyxl==3.1.5",
                "et-xmlfile==2.0.0",
                "",
            ]),
            encoding="utf-8",
        )
    else:
        dest.joinpath("packages_wheel").mkdir(exist_ok=True)
        dest.joinpath("requirements_supplement_en.txt").write_text(
            "\n".join([
                "# No extra Windows wheels for python312 in this round.",
                "# akshare==1.20.8 already in original 16_timeseries_quant_py312 lock.",
                "",
            ]),
            encoding="utf-8",
        )
    dest.joinpath("requirements_supplement_sdist_en.txt").write_text(
        "\n".join([
            "# Source-only. NOT built on the Linux download host. NOT Windows wheels.",
            "# On Windows, after original env exists, you MAY try:",
            "#   python -m pip install --no-index --find-links packages_sdist --find-links <env>\\wheelhouse -r this file",
            "# Status: unbuilt, unverified.",
            "lime==0.2.0.1",
            "ta==0.11.0",
            "jieba==0.42.1",
            "odfpy==1.4.1",
            "jsonpath==0.82.2",
            "",
        ]),
        encoding="utf-8",
    )
    dest.joinpath("packages_sdist" / "UNBUILT_cn.txt" if False else dest.joinpath("UNBUILT_cn.txt")).write_text(
        "lime/ta/jieba/odfpy/jsonpath 仅保存 PyPI 源码包。Linux 下载主机没有为它们构建 win_amd64 wheel。"
        "不能把任何 Linux wheel 当作 Windows 包使用。本轮未在 Windows 上构建或验证。\n",
        encoding="utf-8",
    )
    return rows


def write_inventory(dest: Path, rows: list[dict]) -> None:
    fields = ["file", "title", "kind", "status", "environments", "source", "how", "bytes", "sha256"]
    path = dest / "inventory_cn.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def zip_tree(src: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for dirpath, _, filenames in os.walk(src):
            for name in filenames:
                p = Path(dirpath) / name
                arc = p.relative_to(src.parent).as_posix()
                z.write(p, arc)


def assemble_one(dest: Path, py: str, tag: str) -> int:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for doc in (
        "离线安装与使用_cn.md",
        "常见任务快速入门_cn.md",
        "常用工具与包用途索引_cn.md",
    ):
        shutil.copy2(DOCS / doc, dest / doc)
    write_supplement_readme(dest, py, tag)
    write_ps1(dest, py)
    env_src = ROOT / f"python{py}_amd64" / "environments"
    rd = dest / "env_readme_updated"
    rd.mkdir(parents=True, exist_ok=True)
    for d in sorted(env_src.iterdir()):
        r = d / "README_cn.md"
        if r.is_file():
            shutil.copy2(r, rd / f"{d.name}_README_cn.md")
    rows = copy_externals(dest) + copy_python_artifacts(dest, py)
    write_inventory(dest, rows)
    total = sum(r["bytes"] for r in rows)
    print(f"{dest.name}: files={len(rows)} bytes={total}")
    return total


def main() -> None:
    tag = "wpo-full-20261030"
    for tree, py in ((ROOT / "python310_amd64", "310"), (ROOT / "python312_amd64", "312")):
        env = tree / "environments"
        for d in sorted(env.iterdir()):
            r = d / "README_cn.md"
            if r.is_file():
                append_env_readme(r)
        update_tree_readme(tree, "3.10.11" if py == "310" else "3.12.10", f"python{py}_amd64_supplement")

    overview = ROOT / "environments_overview_cn.md"
    ov = overview.read_text(encoding="utf-8")
    if "定向补充包 v1" not in ov:
        overview.write_text(
            ov.rstrip()
            + "\n\n## 定向补充包 v1（不重新打包原 Release）\n\n"
            + "见 `python310_amd64_supplement/` 与 `python312_amd64_supplement/`。"
            + "原 lock 不变。源码包未构建。必须使用 3.10.11 / 3.12.10，不能装入 3.14。\n",
            encoding="utf-8",
        )

    t310 = assemble_one(OUT310, "310", tag)
    t312 = assemble_one(OUT312, "312", tag)
    DIST.mkdir(exist_ok=True)
    z310 = DIST / "windows_python310_amd64_supplement_v1.zip"
    z312 = DIST / "windows_python312_amd64_supplement_v1.zip"
    print("zip 310...")
    zip_tree(OUT310, z310)
    print("zip 312...")
    zip_tree(OUT312, z312)
    for z in (z310, z312):
        digest = sha256_file(z)
        z.with_suffix(z.suffix + ".sha256").write_text(
            f"{digest}  {z.name}\n", encoding="utf-8"
        )
        print(z.name, z.stat().st_size, digest)
    print("tree310", t310, "tree312", t312)


if __name__ == "__main__":
    main()
