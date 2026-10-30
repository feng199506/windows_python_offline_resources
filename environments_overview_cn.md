# 环境总览

本库是 Windows 通用科研 Python **离线基础环境**，不是历史项目精确复现。  
正式交付两棵独立树：[`python310_amd64/`](python310_amd64/)（CPython 3.10.11）与 [`python312_amd64/`](python312_amd64/)（CPython 3.12.10）。  
本轮状态：已下载官方安装程序与 Windows wheel，并完成静态检查。  
**尚未**在目标 Windows 上安装或运行，因此没有任何一组可标记为“安装验证通过”。

## Python 选择

| 解释器 | 安装程序 | 角色 |
| --- | --- | --- |
| CPython 3.10.11 x64 | [`python310_amd64/runtime/python-3.10.11-amd64.exe`](python310_amd64/runtime/python-3.10.11-amd64.exe) | 旧项目复现。**2026-10-01 已结束安全支持**。 |
| CPython 3.12.10 x64 | [`python312_amd64/runtime/python-3.12.10-amd64.exe`](python312_amd64/runtime/python-3.12.10-amd64.exe) | 仍受支持的第二套（至 2028-10）。最后带 Windows 安装程序的 3.12。 |

依据见 [`guides/python_version_policy_cn.md`](guides/python_version_policy_cn.md)。3.10 与 3.12 的 wheel **不能**装进同一 venv。

| 树 | 环境组 | wheel 数 | 体积 |
| --- | --- | --- | --- |
| [`python310_amd64/`](python310_amd64/) | 31 | 1504 | 4.64 GiB |
| [`python312_amd64/`](python312_amd64/) | 31 | 1478 | 5.02 GiB |

wheel 数为各组 wheelhouse 合计（含故意重复的 torch/TF）。明细见各树 [`README_cn.md`](README_cn.md) 与 `tree_stats_en.json`。

## 静态检查实际做了什么

- `pip download --platform win_amd64 --python-version 310|312 --implementation cp --only-binary=:all:`（Linux 主机，Windows 目标），解析并下载全部传递依赖。
- 第二遍读取每个 wheel 的 `Requires-Dist`，按 `sys_platform=win32` 与目标 Python 版本补下载标记依赖。
- 检查每个 `.whl` 可被 zip 打开。
- 平台标签仅为 `win_amd64` 或 `any`；无 manylinux/macOS/sdist 混入。
- 确认无 `onnxruntime-gpu`、无 `+cu` CUDA torch、OpenCV 仅为 headless 4.10。
- 安装程序：3.12.10 的 MD5 与 python.org 发布页一致；3.10.11 页面只公布 MD5，本库记录自算 SHA256。

## 还没做、因此不能声称的事项

- 未在 Windows 上创建 venv、未 `pip install`、未 `import`、未跑训练。
- 未下载模型权重、大型数据集、CUDA、cuDNN、CmdStan、FFmpeg、Graphviz 引擎、Playwright 浏览器。
- 未解包或复现已归档研究项目。
