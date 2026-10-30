#!/usr/bin/env python3
"""Incrementally add new Windows offline environment groups.

Does not re-download existing environments. Downloads target packages,
declared extras, and pip-resolved transitive wheels for win_amd64.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_environments import (  # noqa: E402
    ENV_ROOT,
    PROJ_ROOT,
    ROOT,
    STATE,
    PYTHON,
    PIP_PYZ,
    download_wheels,
    env_dir,
    lockfile_from_wheels,
    marker_path,
    pip_cmd,
    run,
    wheelhouse,
    write_requirements,
    write_scripts,
    write_wheel_manifest,
)

BOOT = ["pip", "setuptools", "wheel", "packaging"]

NEW_ENVIRONMENTS = [
    {
        "id": "12_scientific_extra_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "科学计算扩展",
        "purpose_cn": "Numba、Dask、Polars、Zarr、PyTables、地理空间等。不含已有基础 Notebook 全集。",
        "framework": "numba/dask/polars/geopandas/zarr",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "numpy", "scipy", "pandas", "pyarrow",
            "numba", "bottleneck", "numexpr",
            "dask[array,dataframe,distributed]",
            "polars",
            "zarr", "tables", "sparse",
            "astropy", "pint", "uncertainties", "lmfit",
            "shapely", "pyproj", "geopandas", "fiona", "rasterio", "rtree",
            "igraph", "networkx",
        ],
        "imports": ["numba", "dask", "polars", "zarr", "tables", "geopandas", "shapely", "astropy"],
        "gpu": False,
    },
    {
        "id": "13_stats_optimize_extra_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "统计与优化扩展",
        "purpose_cn": "生存分析、计量、超参优化、cvxopt。与 11_optimization_control 的 CVXPY/CasADi 分开。",
        "framework": "pingouin/lifelines/optuna/cvxopt/pymoo",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "numpy", "scipy", "pandas", "matplotlib", "scikit-learn", "statsmodels",
            "pingouin", "lifelines", "linearmodels", "arch",
            "optuna", "hyperopt", "scikit-optimize", "cvxopt", "nevergrad", "pymoo",
        ],
        "imports": ["pingouin", "lifelines", "linearmodels", "arch", "optuna", "cvxopt", "pymoo"],
        "gpu": False,
    },
    {
        "id": "14_ml_extra_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "传统机器学习扩展",
        "purpose_cn": "不平衡学习、编码、解释性、流形与密度聚类。不含 xgboost/lightgbm/catboost 全集。",
        "framework": "imbalanced-learn/shap/umap/hdbscan",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "numpy", "scipy", "pandas", "matplotlib", "scikit-learn",
            "imbalanced-learn", "category-encoders", "shap", "lime", "mlxtend",
            "umap-learn", "hdbscan", "yellowbrick", "feature-engine", "kmodes", "prince",
        ],
        "imports": ["imblearn", "category_encoders", "shap", "lime", "umap", "hdbscan"],
        "gpu": False,
    },
    {
        "id": "15_dl_pytorch_extra_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "深度学习扩展（PyTorch CPU）",
        "purpose_cn": "Lightning、timm、kornia、einops。独立于 04 基础 PyTorch 环境；不含 CUDA。",
        "framework": "lightning/timm/kornia + torch CPU",
        "index_url": "https://download.pytorch.org/whl/cpu",
        "extra_index": ["https://pypi.org/simple"],
        "packages": BOOT + [
            "numpy", "torch", "torchvision",
            "lightning", "torchmetrics", "einops", "timm", "kornia",
        ],
        "imports": ["torch", "lightning", "torchmetrics", "einops", "timm", "kornia"],
        "gpu": False,
        "source_note": "torch from PyTorch CPU index; extras from PyPI.",
    },
    {
        "id": "16_timeseries_quant_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "时间序列与量化",
        "purpose_cn": "ARIMA/Prophet/tsfresh、行情接口与回测基础。不含券商终端或权重。",
        "framework": "pmdarima/prophet/tsfresh/yfinance/backtrader",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "numpy", "pandas", "scipy", "statsmodels", "scikit-learn",
            "pmdarima", "prophet", "tsfresh",
            "yfinance", "akshare", "exchange-calendars",
            "backtrader", "ta", "empyrical",
        ],
        "imports": ["pmdarima", "prophet", "tsfresh", "yfinance", "akshare", "backtrader"],
        "gpu": False,
    },
    {
        "id": "17_nlp_classic_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "NLP 经典工具（无权重、无 PyTorch）",
        "purpose_cn": "NLTK/spaCy/Gensim/jieba。spaCy 模型与 NLTK 语料不下载。",
        "framework": "nltk/spacy/gensim/jieba",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "numpy", "nltk", "spacy", "gensim", "jieba", "textblob", "wordcloud", "regex", "lxml",
        ],
        "imports": ["nltk", "spacy", "gensim", "jieba", "textblob", "wordcloud"],
        "gpu": False,
    },
    {
        "id": "17b_nlp_sentence_transformers_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "NLP Sentence-Transformers（CPU，不含权重）",
        "purpose_cn": "与经典 NLP 及 Hugging Face 基础环境分开，避免与无 torch 组混装。",
        "framework": "sentence-transformers + torch CPU",
        "index_url": "https://download.pytorch.org/whl/cpu",
        "extra_index": ["https://pypi.org/simple"],
        "packages": BOOT + ["numpy", "torch", "sentence-transformers"],
        "imports": ["torch", "sentence_transformers"],
        "gpu": False,
    },
    {
        "id": "18_vision_extra_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "计算机视觉扩展",
        "purpose_cn": "OCR 封装、哈希、RAW。不与 03 的 OpenCV headless 混装 contrib。Tesseract/Poppler 二进制另列。",
        "framework": "pytesseract/rawpy/imageHash",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "numpy", "Pillow", "pytesseract", "piexif", "ImageHash", "rawpy", "img2pdf", "imageio",
        ],
        "imports": ["pytesseract", "piexif", "imagehash", "rawpy", "img2pdf"],
        "gpu": False,
    },
    {
        "id": "19_av_extra_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "音视频扩展",
        "purpose_cn": "PyAV、MoviePy、pydub 等 Python 封装。FFmpeg 可执行文件不下载。",
        "framework": "av/moviepy/pydub/mutagen",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "numpy", "Pillow", "av", "moviepy", "mutagen", "pydub",
            "ffmpeg-python", "imageio-ffmpeg", "imageio",
        ],
        "imports": ["av", "moviepy", "mutagen", "pydub"],
        "gpu": False,
    },
    {
        "id": "20_web_api_extra_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "Web / API 扩展",
        "purpose_cn": "Flask/Django/Celery。与 10 的 FastAPI/Gradio/Streamlit 分开。不含 gunicorn（非 Windows 首选）。",
        "framework": "flask/django/aiohttp/celery",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "flask[async]", "django", "waitress", "aiohttp",
            "celery[redis]", "redis", "graphene", "marshmallow",
            "httpx", "requests", "uvicorn",
        ],
        "imports": ["flask", "django", "aiohttp", "celery", "redis", "graphene"],
        "gpu": False,
    },
    {
        "id": "21_database_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "数据库",
        "purpose_cn": "SQLAlchemy、驱动与 DuckDB。数据库服务器本身不下载。",
        "framework": "sqlalchemy/psycopg/duckdb/pymongo",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "sqlalchemy[asyncio]", "alembic", "greenlet", "aiosqlite",
            "psycopg[binary]", "pymysql", "pymongo", "redis",
            "duckdb", "pyodbc", "peewee", "sqlite-utils", "elasticsearch",
        ],
        "imports": ["sqlalchemy", "alembic", "psycopg", "pymysql", "pymongo", "duckdb", "redis"],
        "gpu": False,
    },
    {
        "id": "22_crawler_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "爬虫与 Selenium",
        "purpose_cn": "Scrapy/Selenium。浏览器二进制另列。Playwright 见独立环境。",
        "framework": "scrapy/selenium/bs4/lxml",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "scrapy", "beautifulsoup4", "lxml", "selenium",
            "fake-useragent", "PySocks", "feedparser", "httpx", "requests",
        ],
        "imports": ["scrapy", "bs4", "lxml", "selenium"],
        "gpu": False,
    },
    {
        "id": "22b_playwright_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "Playwright Python 包",
        "purpose_cn": "仅 Python wheel。Chromium/Firefox/WebKit 需日后 playwright install，不算已下载依赖。",
        "framework": "playwright",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + ["playwright"],
        "imports": ["playwright"],
        "gpu": False,
    },
    {
        "id": "23_office_pdf_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "Office / PDF",
        "purpose_cn": "docx/pptx/xlsx/PDF 解析生成。WeasyPrint/tabula/camelot 因系统库或 Java 另列。",
        "framework": "python-docx/pypdf/reportlab/pdfplumber",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "python-docx", "python-pptx", "xlsxwriter", "xlrd", "odfpy",
            "reportlab", "pypdf", "pdfminer.six", "pdfplumber", "fpdf2",
            "mammoth", "openpyxl", "Pillow",
        ],
        "imports": ["docx", "pptx", "xlsxwriter", "pypdf", "pdfminer", "pdfplumber", "reportlab"],
        "gpu": False,
    },
    {
        "id": "24_gui_tk_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "桌面 GUI（Tk 路线）",
        "purpose_cn": "customtkinter/ttkbootstrap。与 Qt/wx 分开。",
        "framework": "customtkinter/ttkbootstrap",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + ["customtkinter", "ttkbootstrap", "Pillow"],
        "imports": ["customtkinter", "ttkbootstrap"],
        "gpu": False,
    },
    {
        "id": "24b_gui_pyqt6_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "桌面 GUI（PyQt6）",
        "purpose_cn": "不与 PySide6 或 wxPython 混装。",
        "framework": "PyQt6",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + ["PyQt6"],
        "imports": ["PyQt6"],
        "gpu": False,
    },
    {
        "id": "24c_gui_pyside6_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "桌面 GUI（PySide6）",
        "purpose_cn": "不与 PyQt6 混装。",
        "framework": "PySide6",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + ["PySide6"],
        "imports": ["PySide6"],
        "gpu": False,
    },
    {
        "id": "24d_gui_wx_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "桌面 GUI（wxPython）",
        "purpose_cn": "独立环境。无 wheel 则记录并跳过。",
        "framework": "wxPython",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + ["wxPython"],
        "imports": ["wx"],
        "gpu": False,
    },
    {
        "id": "25_devtools_py310",
        "root": ENV_ROOT,
        "py": "310",
        "title_cn": "开发测试与打包工具",
        "purpose_cn": "pytest/ruff/mypy/sphinx/pyinstaller 等。",
        "framework": "pytest/ruff/mypy/pyinstaller/sphinx",
        "index_url": "https://pypi.org/simple",
        "extra_index": [],
        "packages": BOOT + [
            "pytest", "pytest-cov", "pytest-xdist", "pytest-asyncio",
            "hypothesis", "coverage", "tox", "nox",
            "black", "ruff", "isort", "mypy", "pylint", "flake8",
            "build", "twine", "hatch", "pyinstaller",
            "pre-commit", "sphinx", "mkdocs", "mkdocs-material",
            "cookiecutter", "pip-tools", "ipython", "ipdb",
        ],
        "imports": ["pytest", "hypothesis", "black", "ruff", "mypy", "sphinx", "PyInstaller"],
        "gpu": False,
    },
]


def download_one_spec(spec: dict, package: str) -> tuple[bool, str]:
    dest = wheelhouse(spec)
    dest.mkdir(parents=True, exist_ok=True)
    log = env_dir(spec) / "download_log_en.txt"
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
        package,
    ]
    for extra in spec.get("extra_index", []):
        cmd.extend(["--extra-index-url", extra])
    proc = run(cmd, log)
    if proc.returncode == 0:
        return True, "ok"
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    return False, text[-2000:]


def prepare_new(spec: dict) -> dict:
    d = env_dir(spec)
    d.mkdir(parents=True, exist_ok=True)
    mark = marker_path(spec)
    if mark.exists() and json.loads(mark.read_text(encoding="utf-8")).get("status") == "downloaded":
        print(f"SKIP {spec['id']}")
        n, total, _ = write_wheel_manifest(spec)
        return {"environment": spec["id"], "status": "skipped_existing", "wheel_count": n, "total_bytes": total, "failed": []}

    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_scripts(spec)
    failed: list[dict] = []
    ok, detail = download_wheels(spec, spec["packages"])
    resolved = list(spec["packages"])
    if not ok:
        print(f"{spec['id']} group resolve failed, falling back per-package")
        # keep any wheels already fetched; try each direct spec
        resolved = []
        for pkg in spec["packages"]:
            pok, pdetail = download_one_spec(spec, pkg)
            if pok:
                resolved.append(pkg)
                print(f"  OK {pkg}")
            else:
                failed.append({"package": pkg, "detail": pdetail[-800:]})
                print(f"  FAIL {pkg}")
        write_requirements(spec, resolved or spec["packages"])

    n, total, rows = write_wheel_manifest(spec)
    if n:
        lockfile_from_wheels(spec)
        lock = d / "requirements_lock_en.txt"
        txt = lock.read_text(encoding="utf-8")
        if "transitive" not in txt:
            txt = txt.replace(
                "Do not mix with GPU or Linux wheels.\n",
                "Do not mix with GPU or Linux wheels.\n"
                "# Includes direct packages AND all resolved Windows transitive dependencies.\n",
            )
            lock.write_text(txt, encoding="utf-8")
        status = "downloaded"
    else:
        status = "failed"
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    result = {
        "environment": spec["id"],
        "status": status,
        "python": spec["py"],
        "direct_ok": resolved,
        "failed": failed,
        "wheel_count": n,
        "total_bytes": total,
        "started_utc": started,
        "finished_utc": finished,
        "notes": "expansion round; Windows install not verified",
    }
    mark.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    results = []
    for spec in NEW_ENVIRONMENTS:
        print(f"\n===== {spec['id']} =====")
        results.append(prepare_new(spec))
        (STATE / "expand_last.json").write_text(
            json.dumps({k: v for k, v in results[-1].items() if k != "failed"}, indent=2),
            encoding="utf-8",
        )
    (STATE / "expand_results_en.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for r in results:
        print(f"{r['environment']}: {r['status']} wheels={r['wheel_count']} failed={len(r.get('failed') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
