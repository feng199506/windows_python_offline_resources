# Python 3.10.11 / Windows amd64 离线套件

独立目录：`windows_python_offline_resources/python310_amd64/`  
不依赖 [`python312_amd64/`](../python312_amd64/) 或其他版本目录。拷到 Windows 后只用本树即可安装。

| 项 | 值 |
| --- | --- |
| CPython | **3.10.11**（有 python.org 官方 Windows x64 `.exe` 的最后一版；其后 3.10.x 仅为源码） |
| 架构 | amd64（win_amd64 / x86-64） |
| 安装程序 | [`runtime/python-3.10.11-amd64.exe`](runtime/python-3.10.11-amd64.exe)（SHA256 `d8dede5005564b408ba50317108b765ed9c3c510342a598f9fd42681cbe0648b`） |
| VC++ | [`runtime/vc_redist.x64.exe`](runtime/vc_redist.x64.exe) |
| 环境组 | **31** |
| wheel 合计 | **1504**（分组存放，torch/TF 等故意重复） |
| wheel 体积 | **4.64 GiB** |
| 本轮 | 已按 `win_amd64` + CPython 3.10 下载并写锁定清单；**未**在 Windows 上安装验证 |

3.10 已于 **2026-10-01** 结束安全支持，本套仅用于兼容旧代码。

## 安装

```powershell
# 1. 安装 runtime\python-3.10.11-amd64.exe 与 vc_redist.x64.exe
# 2. 选一个环境：
cd environments\01_base_scientific_py310
powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1 -PythonExe "C:\Python310\python.exe"
.\.venv\Scripts\python.exe .\check_environment_en.py
```

使用 `requirements_lock_en.txt`（含传递依赖），不要只装 direct 清单。

## 各组

| 组 | 路径 | wheel | 大小 |
| --- | --- | --- | --- |
| 基础科学计算与 Notebook | [`environments/01_base_scientific_py310/`](environments/01_base_scientific_py310/) | 131 | 208.7 MiB |
| 传统 ML / 统计 / EM | [`environments/02_ml_stats_py310/`](environments/02_ml_stats_py310/) | 38 | 305.1 MiB |
| 信号 / 音频 / 图像 | [`environments/03_signal_image_audio_py310/`](environments/03_signal_image_audio_py310/) | 74 | 204.7 MiB |
| PyTorch CPU | [`environments/04_pytorch_cpu_py310/`](environments/04_pytorch_cpu_py310/) | 17 | 143.7 MiB |
| GPR / BO（PyTorch） | [`environments/05_gpr_bo_pytorch_py310/`](environments/05_gpr_bo_pytorch_py310/) | 36 | 197.5 MiB |
| 贝叶斯 / MCMC | [`environments/06_bayesian_mc_py310/`](environments/06_bayesian_mc_py310/) | 46 | 92.9 MiB |
| TensorFlow CPU | [`environments/07_tensorflow_cpu_py310/`](environments/07_tensorflow_cpu_py310/) | 33 | 388.5 MiB |
| GPflow 专用 | [`environments/07b_gpflow_tf_py310/`](environments/07b_gpflow_tf_py310/) | 53 | 471.9 MiB |
| 强化学习基础 | [`environments/08_rl_basic_py310/`](environments/08_rl_basic_py310/) | 40 | 183.8 MiB |
| Hugging Face CPU | [`environments/09_huggingface_llm_cpu_py310/`](environments/09_huggingface_llm_cpu_py310/) | 64 | 199.4 MiB |
| ONNX CPU / API / UI | [`environments/10_onnx_api_app_py310/`](environments/10_onnx_api_app_py310/) | 86 | 181.9 MiB |
| 优化与控制 | [`environments/11_optimization_control_py310/`](environments/11_optimization_control_py310/) | 28 | 139.6 MiB |
| 科学计算扩展 | [`environments/12_scientific_extra_py310/`](environments/12_scientific_extra_py310/) | 83 | 299.6 MiB |
| 统计与优化扩展 | [`environments/13_stats_optimize_extra_py310/`](environments/13_stats_optimize_extra_py310/) | 70 | 131.1 MiB |
| 传统 ML 扩展 | [`environments/14_ml_extra_py310/`](environments/14_ml_extra_py310/) | 54 | 152.4 MiB |
| 深度学习扩展 | [`environments/15_dl_pytorch_extra_py310/`](environments/15_dl_pytorch_extra_py310/) | 48 | 160.3 MiB |
| 时间序列与量化 | [`environments/16_timeseries_quant_py310/`](environments/16_timeseries_quant_py310/) | 68 | 176.1 MiB |
| NLP 经典 | [`environments/17_nlp_classic_py310/`](environments/17_nlp_classic_py310/) | 68 | 132.0 MiB |
| Sentence-Transformers | [`environments/17b_nlp_sentence_transformers_py310/`](environments/17b_nlp_sentence_transformers_py310/) | 45 | 204.5 MiB |
| 计算机视觉扩展 | [`environments/18_vision_extra_py310/`](environments/18_vision_extra_py310/) | 16 | 74.0 MiB |
| 音视频扩展 | [`environments/19_av_extra_py310/`](environments/19_av_extra_py310/) | 19 | 79.6 MiB |
| Web / API | [`environments/20_web_api_extra_py310/`](environments/20_web_api_extra_py310/) | 56 | 16.3 MiB |
| 数据库 | [`environments/21_database_py310/`](environments/21_database_py310/) | 39 | 26.0 MiB |
| 爬虫与 Selenium | [`environments/22_crawler_py310/`](environments/22_crawler_py310/) | 68 | 29.9 MiB |
| Playwright Python | [`environments/22b_playwright_py310/`](environments/22b_playwright_py310/) | 8 | 40.1 MiB |
| Office / PDF | [`environments/23_office_pdf_py310/`](environments/23_office_pdf_py310/) | 27 | 33.2 MiB |
| GUI Tk | [`environments/24_gui_tk_py310/`](environments/24_gui_tk_py310/) | 8 | 10.4 MiB |
| GUI PyQt6 | [`environments/24b_gui_pyqt6_py310/`](environments/24b_gui_pyqt6_py310/) | 7 | 85.4 MiB |
| GUI PySide6 | [`environments/24c_gui_pyside6_py310/`](environments/24c_gui_pyside6_py310/) | 11 | 249.9 MiB |
| GUI wxPython | [`environments/24d_gui_wx_py310/`](environments/24d_gui_wx_py310/) | 7 | 34.1 MiB |
| 开发测试工具 | [`environments/25_devtools_py310/`](environments/25_devtools_py310/) | 156 | 97.1 MiB |

## 未下载（无兼容 win_amd64 wheel）

lime（14）、akshare / ta（16）、jieba（17）、odfpy（23）。这些包在 PyPI 上没有可用于 `--only-binary=:all:` 的 Windows wheel。

## 限制

- 未在目标 Windows 上创建 venv、未 `pip install`、未 `import`。
- 无 CUDA / GPU wheel。
- GPflow（07b）锁定 TF 2.16.2 + numpy&lt;2，不能与 07 的 TF 2.21 混装。
