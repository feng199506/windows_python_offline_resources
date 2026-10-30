# Python 3.12.10 / Windows amd64 离线套件

独立目录：`windows_python_offline_resources/python312_amd64/`  
不依赖 [`python310_amd64/`](../python310_amd64/) 或其他版本目录。拷到 Windows 后只用本树即可安装。

| 项 | 值 |
| --- | --- |
| CPython | **3.12.10**（有 python.org 官方 Windows x64 `.exe` 的最后一版；其后 3.12.x 仅为源码安全修复） |
| 架构 | amd64（win_amd64 / x86-64） |
| 安装程序 | [`runtime/python-3.12.10-amd64.exe`](runtime/python-3.12.10-amd64.exe)（26 964 224 字节；SHA256 `67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb`；发布页 MD5 `5eddb0b6f12c852725de071ae681dde4` 已核对） |
| VC++ | [`runtime/vc_redist.x64.exe`](runtime/vc_redist.x64.exe) |
| 环境组 | **31** |
| wheel 合计 | **1478**（分组存放，torch/TF 等故意重复） |
| wheel 体积 | **5.02 GiB** |
| 本轮 | 已按 `win_amd64` + CPython 3.12 下载并写锁定清单；**未**在 Windows 上安装验证 |

3.12 安全支持至 **2028-10**。本套与 3.10 套件平行，不要把两边的 wheel 装进同一个 venv。

## 安装

```powershell
# 1. 安装 runtime\python-3.12.10-amd64.exe 与 vc_redist.x64.exe
# 2. 选一个环境：
cd environments\01_base_scientific_py312
powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1 -PythonExe "C:\Python312\python.exe"
.\.venv\Scripts\python.exe .\check_environment_en.py
```

使用 `requirements_lock_en.txt`（含传递依赖），不要只装 direct 清单。

## 各组

| 组 | 路径 | wheel | 大小 | 说明 |
| --- | --- | --- | --- | --- |
| 基础科学计算与 Notebook | [`environments/01_base_scientific_py312/`](environments/01_base_scientific_py312/) | 127 | 206.7 MiB | numpy 2.5.4、scipy 1.18.1、pandas 3.1.0、jupyterlab 4.6.5 |
| 传统 ML / 统计 / EM | [`environments/02_ml_stats_py312/`](environments/02_ml_stats_py312/) | 38 | 252.2 MiB | scikit-learn 1.9.1 |
| 信号 / 音频 / 图像 | [`environments/03_signal_image_audio_py312/`](environments/03_signal_image_audio_py312/) | 70 | 200.6 MiB | opencv-python-headless 4.10.0.84 |
| PyTorch CPU | [`environments/04_pytorch_cpu_py312/`](environments/04_pytorch_cpu_py312/) | 17 | 144.5 MiB | torch 2.11.0+cpu |
| GPR / BO（PyTorch） | [`environments/05_gpr_bo_pytorch_py312/`](environments/05_gpr_bo_pytorch_py312/) | 32 | 194.0 MiB | 与 GPflow 分开 |
| 贝叶斯 / MCMC | [`environments/06_bayesian_mc_py312/`](environments/06_bayesian_mc_py312/) | 42 | 129.3 MiB | CmdStan 本体未打包 |
| TensorFlow CPU | [`environments/07_tensorflow_cpu_py312/`](environments/07_tensorflow_cpu_py312/) | 33 | 389.0 MiB | tensorflow-cpu 2.21.0、keras 3.15.1 |
| GPflow 专用 | [`environments/07b_gpflow_tf_py312/`](environments/07b_gpflow_tf_py312/) | 62 | 879.5 MiB | TF-intel 2.16.2、numpy 1.26.4；不要与 07 混装 |
| 强化学习基础 | [`environments/08_rl_basic_py312/`](environments/08_rl_basic_py312/) | 39 | 184.9 MiB | 无 MuJoCo/Atari |
| Hugging Face CPU | [`environments/09_huggingface_llm_cpu_py312/`](environments/09_huggingface_llm_cpu_py312/) | 60 | 199.5 MiB | transformers 5.22.0；**不含权重** |
| ONNX CPU / API / UI | [`environments/10_onnx_api_app_py312/`](environments/10_onnx_api_app_py312/) | 77 | 176.7 MiB | onnxruntime 1.31.1 |
| 优化与控制 | [`environments/11_optimization_control_py312/`](environments/11_optimization_control_py312/) | 31 | 140.5 MiB | cvxpy 1.9.3 |
| 科学计算扩展 | [`environments/12_scientific_extra_py312/`](environments/12_scientific_extra_py312/) | 89 | 303.4 MiB | numba/dask/polars/geopandas |
| 统计与优化扩展 | [`environments/13_stats_optimize_extra_py312/`](environments/13_stats_optimize_extra_py312/) | 68 | 127.9 MiB | optuna/cvxopt 等 |
| 传统 ML 扩展 | [`environments/14_ml_extra_py312/`](environments/14_ml_extra_py312/) | 53 | 148.2 MiB | 无 lime（无 win wheel） |
| 深度学习扩展 | [`environments/15_dl_pytorch_extra_py312/`](environments/15_dl_pytorch_extra_py312/) | 45 | 161.8 MiB | Lightning 等 |
| 时间序列与量化 | [`environments/16_timeseries_quant_py312/`](environments/16_timeseries_quant_py312/) | 77 | 202.8 MiB | 无 ta（无 win wheel）；akshare 已下 |
| NLP 经典 | [`environments/17_nlp_classic_py312/`](environments/17_nlp_classic_py312/) | 67 | 128.1 MiB | 无 jieba（无 win wheel） |
| Sentence-Transformers | [`environments/17b_nlp_sentence_transformers_py312/`](environments/17b_nlp_sentence_transformers_py312/) | 44 | 200.3 MiB | 不含权重 |
| 计算机视觉扩展 | [`environments/18_vision_extra_py312/`](environments/18_vision_extra_py312/) | 16 | 69.7 MiB | |
| 音视频扩展 | [`environments/19_av_extra_py312/`](environments/19_av_extra_py312/) | 19 | 79.3 MiB | 系统 FFmpeg 未打包 |
| Web / API | [`environments/20_web_api_extra_py312/`](environments/20_web_api_extra_py312/) | 53 | 16.4 MiB | |
| 数据库 | [`environments/21_database_py312/`](environments/21_database_py312/) | 36 | 28.3 MiB | |
| 爬虫与 Selenium | [`environments/22_crawler_py312/`](environments/22_crawler_py312/) | 65 | 29.8 MiB | 浏览器未打包 |
| Playwright Python | [`environments/22b_playwright_py312/`](environments/22b_playwright_py312/) | 8 | 40.1 MiB | **不含**浏览器二进制 |
| Office / PDF | [`environments/23_office_pdf_py312/`](environments/23_office_pdf_py312/) | 26 | 34.1 MiB | 无 odfpy（无 win wheel） |
| GUI Tk | [`environments/24_gui_tk_py312/`](environments/24_gui_tk_py312/) | 8 | 10.5 MiB | 与 Qt/wx 分开 |
| GUI PyQt6 | [`environments/24b_gui_pyqt6_py312/`](environments/24b_gui_pyqt6_py312/) | 7 | 85.4 MiB | |
| GUI PySide6 | [`environments/24c_gui_pyside6_py312/`](environments/24c_gui_pyside6_py312/) | 10 | 249.9 MiB | |
| GUI wxPython | [`environments/24d_gui_wx_py312/`](environments/24d_gui_wx_py312/) | 6 | 33.5 MiB | |
| 开发测试工具 | [`environments/25_devtools_py312/`](environments/25_devtools_py312/) | 153 | 97.5 MiB | |

## 未下载（无兼容 win_amd64 wheel）

| 包 | 组 | 说明 |
| --- | --- | --- |
| lime | 14 | 仅 sdist，`--only-binary=:all:` 不下 |
| ta | 16 | 同上 |
| jieba | 17 | 同上 |
| odfpy | 23 | 同上 |
| tensorflow-io-gcs-filesystem | 07b | TF 2.16 仅对 Python&lt;3.12 声明需要；3.12 无对应 Windows wheel，也不需要 |

## 限制

- 未在目标 Windows 上创建 venv、未 `pip install`、未 `import`。
- 无 CUDA / GPU wheel。TF 原生 Windows GPU 不在本套范围内。
- Playwright 浏览器、FFmpeg、CmdStan、Graphviz 引擎、模型权重另见库根 [`external_dependencies_cn.csv`](../external_dependencies_cn.csv)。

## 本轮定向补充

原锁定清单未改。新增内容在独立目录 [`python312_amd64_supplement/`](../python312_amd64_supplement/)（随补充 zip 发布，原 Release tar 不变）。

| 类别 | 内容 |
| --- | --- |
| 已下载 wheel | 原 31 组 wheelhouse；3.10 另补 `akshare==1.18.88` 及部分依赖 wheel |
| 源码待构建 | lime 0.2.0.1、ta 0.11.0、jieba 0.42.1、odfpy 1.4.1、jsonpath 0.82.2（**未构建、未验证**，不是 Linux wheel） |
| 已下载外部工具 | Chrome for Testing 156.0.8078.4、chromedriver、headless-shell、geckodriver 0.37.1、msedgedriver 156.0.4314.50、Playwright Firefox/WebKit/ffmpeg、FFmpeg 9.0.2 essentials、Tesseract 5.4.0 与 eng/chi_sim/chi_tra/osd |
| 仍缺失 | Playwright 官方 Chromium rev 1248 zip、完整 Firefox 安装包、CmdStan 工具链、CUDA、HF/spaCy/NLTK 数据、串口/烧录工具、数据库服务器 |

必须用 [`runtime/python-3.12.10-amd64.exe`](runtime/python-3.12.10-amd64.exe) 创建 venv，**不支持直接装入 Python 3.14**。
说明：[`python312_amd64_supplement/离线安装与使用_cn.md`](../python312_amd64_supplement/%E7%A6%BB%E7%BA%BF%E5%AE%89%E8%A3%85%E4%B8%8E%E4%BD%BF%E7%94%A8_cn.md)。
