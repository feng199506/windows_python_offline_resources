# WSL2 / Linux 可选说明

有些组件在 Windows 原生环境没有可用 wheel、需要 Linux 系统库，或官方已改为只在 WSL2 提供 GPU。这些内容**不得**并入 [`environments/`](../environments/) 的 Windows wheelhouse。

本轮不安装 WSL2，不下载 Linux wheel，不运行 Linux 项目代码。

## 何时使用 WSL2

- TensorFlow GPU（TF 2.11 及以后的官方 GPU 路线）
- 仅发布 `manylinux` wheel、没有 `win_amd64` 的包
- 需要 gcc/gfortran、系统共享库、或 Linux 专用仿真器的项目
- PyMC/PyTensor 要大规模编译自定义算子，而本机没有 Windows C++ 工具链时

## TensorFlow GPU（WSL2）

与原生 Windows 历史 GPU（TF≤2.10）分开：

| 路线 | 位置 | TF 版本线索 | 本轮 |
| --- | --- | --- | --- |
| 原生 Windows GPU | 仅旧实验 | TF 2.10 及更早 | 不下载 |
| 原生 Windows CPU | `environments/07_tensorflow_cpu_py310` | TF 2.21 CPU / tensorflow-intel | 已下载 CPU wheel |
| WSL2 Linux GPU | 本目录未来的 Linux 清单 | 官方当前 GPU 构建 | 不下载 |

WSL2 内应按 TensorFlow 官方 Linux GPU 文档安装：NVIDIA 驱动（Windows 侧）+ WSL2 CUDA 用户态 + Linux `tensorflow` GPU wheel。不要把 Linux `manylinux` wheel 拷进 Windows venv。

预留（未创建 wheelhouse）：

```text
wsl2_optional/tensorflow_gpu_linux_py310/requirements_direct_en.txt
```

该文件仅作占位提示，见同目录 [`tensorflow_gpu_linux_py310_requirements_en.txt`](tensorflow_gpu_linux_py310_requirements_en.txt)。

## 可能需要 WSL2 或编译的组件

详见 `../compatibility_issues_cn.csv` 与 `../external_dependencies_cn.csv`。常见项：

- CmdStan（C++ 工具链，cmdstanpy 只是 Python 封装）
- 部分仿真器（MuJoCo、Atari ROM、部分物理引擎）
- 无 Windows wheel 的科学包历史版本
- 需要系统 FFmpeg 开发库才能从源码编译的音频扩展（wheel 可用时不必）

## 与基础环境的关系

在 WSL2 中应新建独立 venv，不要尝试“升级” Windows 离线环境。补依赖时只针对即将运行的那一个 Release，对照基础环境后另建项目环境。
