# 信号处理、音频及图像处理

- 环境编号：[`03_signal_image_audio_py312`](./)
- 目标：Windows 10/11 x86-64，CPython 3.12
- 用途：使用 opencv-python-headless，不与 opencv-python / opencv-contrib-python 混装。
- 框架：opencv-headless/scikit-image/librosa/mne
- 本轮状态：**已下载并静态检查**。尚未在目标 Windows 上安装验证。

## 包含内容

- [`requirements_direct_en.txt`](requirements_direct_en.txt)：直接依赖（解析输入）
- [`requirements_lock_en.txt`](requirements_lock_en.txt)：由已下载 wheel 锁定的**完整**版本清单（含全部传递依赖）
- [`wheelhouse/`](wheelhouse/)：目标包及其全部传递依赖的 Windows wheel，文件名为上游原始名称。离线安装时用 `--no-index --find-links wheelhouse -r requirements_lock_en.txt`，不要只装 direct 文件。
- [`wheel_manifest_cn.csv`](wheel_manifest_cn.csv)：包名、版本、标签、大小、SHA256、依赖摘要
- [`install_offline_en.ps1`](install_offline_en.ps1)：离线创建 venv 并安装
- [`check_environment_en.py`](check_environment_en.py)：在 Windows 安装后运行

## 限制

- 这是通用科研基础环境，不是某个历史项目的精确复现。
- 不能与其他 Python 版本、GPU 包或 WSL2/Linux wheel 混装。
- Python 包安装完成不等于权重、数据、编译器或外部服务已具备。
- 包来自 PyPI 或框架官方索引。

## Windows 安装步骤

1. 安装本套件中的 `python-3.12.10-amd64.exe`（独立树用 [`runtime/`](../../runtime/)，库根用 [`installers/`](../../../installers/)）。
2. 安装同位置的 `vc_redist.x64.exe`（多数二进制扩展需要）。
3. 在本目录打开 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1 -PythonExe "C:\Python312\python.exe"
.\.venv\Scripts\python.exe .\check_environment_en.py
```

4. 只有 `check_report_en.json` 中 `ok: true` 且本机实际运行后，才可把该环境记为“安装验证通过”。

## 本组能做什么

OpenCV headless、scikit-image、librosa、MNE 等图像音频信号。

不要与 opencv-python 混装。命令行 FFmpeg 见补充包 19 用途。

## 常用目标包

| 包 | 作用 | 官方文档 |
| --- | --- | --- |
| `opencv-python-headless` | 图像（仅 headless 4.10） | https://docs.opencv.org/ |
| `librosa` | 音频 | https://librosa.org/doc/latest/ |
| `mne` | 脑电/生理信号 | https://mne.tools/stable/ |

其余条目是传递依赖，见 [`requirements_lock_en.txt`](requirements_lock_en.txt)，不逐个说明。
必须使用本树 `runtime` 中的 Python 3.10 或 3.12，不能装进 3.14。
外部工具与未构建源码见同级目录的 `python3xx_amd64_supplement/`。
