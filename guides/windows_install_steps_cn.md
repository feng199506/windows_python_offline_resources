# Windows 安装步骤（通用）

本轮只准备了安装程序和 wheel，**没有**在 Windows 上执行安装。下列步骤供日后在 Windows 10/11 x64 上使用。

## 0. 准备

- 系统：Windows 10 或 11，64 位。
- 不要使用 32 位 Python，不要使用 embeddable 包代替本库中的完整安装程序。
- 管理员权限只用于安装 VC++ / 可选的“为所有用户安装 Python”。创建 venv 不需要管理员权限。
- 两棵树独立：拷 [`python310_amd64/`](../python310_amd64/) **或** [`python312_amd64/`](../python312_amd64/) 即可。

## 1. 安装 Python

- 3.10 树：[`python310_amd64/runtime/python-3.10.11-amd64.exe`](../python310_amd64/runtime/python-3.10.11-amd64.exe)
- 3.12 树：[`python312_amd64/runtime/python-3.12.10-amd64.exe`](../python312_amd64/runtime/python-3.12.10-amd64.exe)

库根 [`installers/`](../installers/) 里是同一文件的副本。

建议：

- 使用完整安装程序（Customize installation → pip、venv、tcl/tk 按需）。
- 可勾选 “Add python.exe to PATH”，或记住安装路径后用全路径调用。
- 3.10 与 3.12 可并存，目录不要互相覆盖。
- Python 3.10 已于 2026-10-01 结束安全支持，仅用于旧项目复现。

## 2. 安装 VC++ 运行库

各树 `runtime/vc_redist.x64.exe`（或 [`installers/vc_redist.x64.exe`](../installers/vc_redist.x64.exe)）。

多数科学计算 wheel 需要它。可先装再装 Python，顺序不严格。

## 3. 可选：Git

[`installers/Git-2.56.0.4-64-bit.exe`](../installers/Git-2.56.0.4-64-bit.exe)

后续按补依赖指南获取单个 Release 时需要。

## 4. 选择一组环境并离线安装

Python 3.12 基础科学计算示例：

```powershell
cd <拷贝后的>\python312_amd64\environments\01_base_scientific_py312
powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1 -PythonExe "C:\Python312\python.exe"
.\.venv\Scripts\python.exe .\check_environment_en.py
```

Python 3.10 则进入 [`python310_amd64\environments\01_base_scientific_py310`](../python310_amd64/environments/01_base_scientific_py310/)，解释器用 `C:\Python310\python.exe`。

脚本行为：

- 用指定解释器新建 venv。
- `pip install --no-index --find-links wheelhouse` 安装 `requirements_lock_en.txt` 中的全部包。
- 失败立即停止，不会改去联网安装。
- 不修改系统 site-packages。

## 5. 检查结果

`check_environment_en.py` 会写出：

- `check_report_en.json`
- `check_report_en.txt`

只有该报告 `ok: true` 且确实运行于目标 Windows 时，才把该环境记为安装验证通过。

## 6. 不要做的事

- 不要把 3.10 与 3.12 的 wheel 装进同一个 venv。
- 不要把 `onnxruntime` 与 `onnxruntime-gpu` 装在一起。
- 不要把 `opencv-python` 与 `opencv-python-headless` 装在一起。
- 不要把 CUDA torch 装进 CPU 环境。
- 不要把 07（TF 2.21）与 07b（TF 2.16 / GPflow）混装。
- 不要运行已下载研究项目里的任意 `install.sh` / `setup.py`。
