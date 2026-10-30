# Python 版本政策

正式交付两棵互不依赖的 Windows x64 树：**3.10.11** 与 **3.12.10**。主机是 Linux，没有本机 Windows Python 可探测，因此按这两版分别下载，不猜测“本机 Windows 版本”，也不下载 3.14。

## CPython 3.10.11（旧代码兼容）

- 目标平台：Windows 10/11 x86-64。
- 安装程序：最后一次为 3.10 发布的官方 Windows x64 完整安装程序。
- 支持状态：PEP 619，安全支持已于 **2026-10-01** 结束。其后 3.10.x 仅为源码，无 Windows 安装程序。
- 目录：[`python310_amd64/`](../python310_amd64/)。
- 不要：把 3.10 当成所有新项目的统一环境；不要把 3.11+ 才支持的包静默混进 3.10 wheelhouse。

## CPython 3.12.10（仍受支持的第二套）

- 选择原因：
  1. 官方仍提供 Windows x64 完整安装程序（3.12.11 起为无安装程序的源码安全包；3.12.10 是最后带 `.exe` 的 3.12）。
  2. 安全支持持续到 **2028-10**。
  3. TensorFlow 2.21、PyTorch 2.11 CPU、主流科学计算包均提供 cp312 `win_amd64` wheel。
- 目录：[`python312_amd64/`](../python312_amd64/)。
- 不要与 3.10 包集合混装。

## 遗留、不是正式第二树

- [`installers/python-3.13.17-amd64.exe`](../installers/python-3.13.17-amd64.exe) 以及 `environments/*_py313/` 是早期试验残留，不纳入两棵正式树。
- 未下载 Python 3.14 / 3.15。

## 需要更高版本的工具

若某工具没有对应 cp310 或 cp312 wheel：

- 记入 [`compatibility_issues_cn.csv`](../compatibility_issues_cn.csv)，不要强装进已有 wheelhouse。
- 需要时在 [`project_specific/`](../project_specific/) 另建环境。
