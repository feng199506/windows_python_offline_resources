# PyTorch CUDA 待选表（未下载）

以官方 Get Started / Previous Versions 为准，选定前核对该日文档：

- https://pytorch.org/get-started/locally/
- https://pytorch.org/get-started/previous-versions/

本轮 **没有** 下载下表中的任何 CUDA wheel。

| 方案编号 | 适用条件 | pip 索引 | 目标 Python | 与本库 CPU 环境关系 | 本轮 |
| --- | --- | --- | --- | --- | --- |
| P-CU-A | NVIDIA GPU + 足够新的 Windows 驱动，官方当前 cu12x | `https://download.pytorch.org/whl/cu126`（以当时文档为准） | 3.10 或 3.13，与 CPU 环境分开 | 新建 `gpu_optional/pytorch_cuXXX_py310/`，不要改 `04_pytorch_cpu_*` | 未下载 |
| P-CU-B | 驱动只支持 CUDA 11.8 | `https://download.pytorch.org/whl/cu118` | 通常 3.10 | 可能无法使用最新 torch，需按官方 previous-versions 锁定 | 未下载 |
| P-CPU | 无 NVIDIA GPU | PyPI / `whl/cpu` | 3.10 或 3.13 | 已准备 CPU 环境 | 已下载 CPU |
| P-WSL2 | 只在 WSL2/Linux 用 GPU | Linux cuXXX 索引 | WSL2 内 Linux Python | 见 [`wsl2_optional/`](../wsl2_optional/)，Windows wheelhouse 不可用 | 未下载 |

选定规则：

1. 先跑 [`collect_windows_hardware_en.ps1`](collect_windows_hardware_en.ps1)。
2. 只选一行。
3. 用 `--platform win_amd64 --python-version 310|313 --only-binary=:all:` 下载。
4. 锁进独立目录，保留官方 `.whl` 文件名。
