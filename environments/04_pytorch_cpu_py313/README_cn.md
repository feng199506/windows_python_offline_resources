# PyTorch CPU（Python 3.13 新项目）

- 环境编号：[`04_pytorch_cpu_py313`](./)
- 目标：Windows 10/11 x86-64，CPython 3.13
- 用途：Python 3.13 Windows CPU 版 PyTorch。
- 框架：torch/torchvision/torchaudio CPU on 3.13
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

1. 安装 [`installers/python-3.13.17-amd64.exe`](../../installers/python-3.13.17-amd64.exe)（勾选 Add python.exe to PATH 可选；建议用完整路径）。
2. 安装 [`installers/vc_redist.x64.exe`](../../installers/vc_redist.x64.exe)（多数二进制扩展需要）。
3. 在本目录打开 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1 -PythonExe "C:\Python313\python.exe"
.\.venv\Scripts\python.exe .\check_environment_en.py
```

4. 只有 `check_report_en.json` 中 `ok: true` 且本机实际运行后，才可把该环境记为“安装验证通过”。
