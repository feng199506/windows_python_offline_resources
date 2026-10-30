# GPU 可选方案（本轮不下载 CUDA 大包）

本目录只提供待选方案和硬件采集步骤。当前机器的 Windows 显卡型号、驱动版本和 CUDA 能力未知，因此**不下载**多套 PyTorch CUDA wheel、TensorFlow GPU 包、cuDNN 或 CUDA Toolkit。

CPU 与 GPU 包必须分开放置，不能写入同一 venv。

## 本轮状态

- 已完成：CPU 环境 wheel 下载与静态检查（见 [`environments/`](../environments/)）。
- 未完成：任何 GPU 包下载、任何 Windows GPU 安装验证。
- 禁止：在未知硬件上猜测 `cu118` / `cu121` / `cu124` / `cu126` 并批量下载。

## 使用前必须先采集硬件

在目标 Windows 上以普通用户运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\collect_windows_hardware_en.ps1
```

将生成的 `hardware_report_en.json` 带回后再选择一套 CUDA 组合。

判定要点：

1. 是否存在 NVIDIA GPU（`nvidia-smi` 能运行）。
2. 驱动版本是否满足所选 PyTorch / TensorFlow 官方表。
3. 是原生 Windows，还是只在 WSL2 中使用 GPU。

AMD / Intel GPU 不走 NVIDIA CUDA 官方 PyTorch 索引。DirectML 等路线需单独评估，本库不预置。

## PyTorch GPU 待选（下载前只保留一套）

官方来源：`https://download.pytorch.org/whl/cuXXX`

待硬件报告后再选 **一行**：

| 条件（示例） | 索引 | 说明 |
| --- | --- | --- |
| 较新 NVIDIA 驱动，官方当前稳定 CUDA 12.x | `https://download.pytorch.org/whl/cu126` 或当时文档指定的 cu12x | 与 CPU 环境的 torch 版本对齐后再锁 |
| 旧驱动，仅支持 CUDA 11.8 | `https://download.pytorch.org/whl/cu118` | 可能只能配较旧 torch，不能强行升级 CPU 环境 |
| 无 NVIDIA GPU | 不要下载任何 `+cu` wheel | 继续使用 `04_pytorch_cpu_py310` |

下载命令模板（Linux 主机、Windows 目标，**选定后再执行**）：

```text
python pip.pyz download --platform win_amd64 --python-version 310 --implementation cp --only-binary=:all: --dest gpu_optional/pytorch_cuXXX_py310/wheelhouse --index-url https://download.pytorch.org/whl/cuXXX --extra-index-url https://pypi.org/simple torch torchvision torchaudio
```

对应 Python 3.13 时把 `--python-version` 改为 `313`，目录不要和 3.10 混用。

## ONNX Runtime GPU 待选

- CPU：`onnxruntime`（已在 `10_onnx_api_app_py310`）
- GPU：`onnxruntime-gpu`
- **两者不能装进同一环境**

在确认 NVIDIA GPU 与驱动后，再单独建 `gpu_optional/onnxruntime_gpu_py310/`。

## TensorFlow GPU：原生 Windows 与 WSL2 必须分开

### 历史：原生 Windows GPU（仅旧版本）

- TensorFlow **2.10 是最后一个支持原生 Windows GPU 的发行版**。
- 2.11 起官方要求：原生 Windows 只用 CPU，或改到 WSL2。
- 可选第三方：`tensorflow-cpu` + TensorFlow-DirectML-Plugin（需另核兼容性，本轮不下载）。

若必须复现 TF≤2.10 的原生 Windows GPU 实验：

- Python 往往要 3.8–3.10，CUDA 11.2 + cuDNN 8.1 一类旧组合。
- 这与本库的 TF 2.21 CPU 环境不兼容，必须新建独立目录，不得升级现有 07 环境。

### 当前：WSL2 中的 TensorFlow GPU

见 [`wsl2_optional/README_cn.md`](../wsl2_optional/README_cn.md)。Linux wheel，不能放入 Windows wheelhouse。

## 本目录预留结构（先空，有硬件报告后再填）

```text
gpu_optional/
  collect_windows_hardware_en.ps1
  README_cn.md
  pytorch_cuda_candidates_cn.md
  (以后) pytorch_cuXXX_py310/   # 只建选定的一套
  (以后) onnxruntime_gpu_py310/
  (以后) tensorflow_native_win_legacy_gpu_py310/  # 仅当必须复现 TF≤2.10
```
