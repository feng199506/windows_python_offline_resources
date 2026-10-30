# 项目补依赖指南

本库是 **Windows 通用科研 Python 离线环境**，不是已归档历史项目的精确复现。以后若要运行某一个 GitHub Release，按本页步骤补齐，**不要直接升级现有基础环境**。

## 原则

1. 只处理用户准备运行的那一个 Release，不要解包全部历史归档。
2. 先对照基础环境，再建立项目专用 venv。
3. 缺什么补什么：Python 包版本、系统库、权重、数据、外部服务。
4. 不得把 GPU 包、另一 Python 版本、或 Linux wheel 混进已有基础环境。
5. Python 包装好不等于可以训练或推理。

## 步骤

### 1. 取单一 Release

只下载将要运行的源代码归档（zip/tar），记录 tag 或提交号。不要为了“调查依赖”而展开全部资料库。

### 2. 静态读取依赖配置

在展开的源码中查找，只读不执行：

- `requirements.txt`、`requirements-*.txt`
- `pyproject.toml`、`setup.cfg`、`setup.py`（只读文本）
- `environment.yml`、Pipfile、poetry.lock、uv.lock
- Dockerfile、README、CI 工作流中的 `pip install` 行

不要运行 `setup.py`、`pip install -e .` 或项目自带安装脚本。

### 3. 对照基础环境

按用途选择最接近的一组：

| 项目类型 | 先对照 |
| --- | --- |
| Notebook / 数据处理 / 绘图 | `01_base_scientific_py310` 或 `01_base_scientific_py313` |
| sklearn / 统计 / 提升树 / HMM | `02_ml_stats_py310` |
| 图像音频信号 | `03_signal_image_audio_py310` |
| PyTorch | `04_pytorch_cpu_py310` 或 `04_pytorch_cpu_py313` |
| GPyTorch / BoTorch | `05_gpr_bo_pytorch_py310` |
| PyMC / Stan / MCMC | `06_bayesian_mc_py310` |
| TensorFlow / Keras | `07_tensorflow_cpu_py310` 或 `07_tensorflow_cpu_py313` |
| GPflow | [`project_specific/07b_gpflow_tf_py310`](project_specific/07b_gpflow_tf_py310/) |
| 强化学习（无大型仿真） | `08_rl_basic_py310` |
| Transformers 等（无权重） | `09_huggingface_llm_cpu_py310` |
| ONNX / FastAPI / Gradio / Streamlit | `10_onnx_api_app_py310` |
| CVXPY / CasADi / python-control | `11_optimization_control_py310` |

对照 `requirements_lock_en.txt` 与 `wheel_manifest_cn.csv`：

- 版本一致：可直接从该组 wheelhouse 离线安装。
- 版本不同但存在 Windows wheel：在 `project_specific/<项目编号>/` **新建**锁定清单并下载缺失 wheel。
- 无 Windows wheel：记录到兼容性问题表，考虑历史 wheel、官方二进制、或 WSL2。不要改基础环境去“迁就”。

### 4. 另建项目环境

```powershell
python.exe -m venv D:\venvs\project_X
.\Scripts\python.exe -m pip install --no-index --find-links <基础或项目 wheelhouse> -r requirements_lock_en.txt
```

目录建议：

```text
windows_python_offline_resources/project_specific/<release_id>/
  requirements_direct_en.txt
  requirements_lock_en.txt
  wheelhouse/
  README_cn.md
```

### 5. 系统库、权重与数据

对照 [`external_dependencies_cn.csv`](external_dependencies_cn.csv)：

- VC++ 运行库、Git：本轮已提供安装程序。
- FFmpeg、Graphviz、CmdStan、CUDA：按项目需要再取官方包。
- 模型权重与数据集：按该 Release 文档单独下载到项目数据目录，不要写入基础 wheelhouse。

### 6. 验证

只有在目标 Windows 上运行项目自带的最小示例或本库 `check_environment_en.py` 之后，才能标记“安装验证通过”。本轮下载主机上的静态检查不能代替这一步。
