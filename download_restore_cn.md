# 下载与解压说明（Windows 通用科研 Python 离线环境库 r2，含补充包）

本 Release（`wpo-full-20261030-r2`）是 2026-10-30 资料库更新后的完整版，包含原来的两棵版本树和定向补充包。它与旧 Release `wpo-full-20261030` 互相独立，只用本 Release 就够了。**不要把两个 Release 的包混在同一个目录解压。**

所有 tar 包都没有压缩，全部解压到**同一个目录**，例如 `D:\wpo\`。目录越短越好：在 `D:\wpo\` 下，包内路径不会超过 Windows 的 260 字符限制。

## 包的分工

r2 把文本和二进制分开打包：

- **01 文档包（必下，约 11 MiB）**：所有说明、离线首页 `index_cn.html`、HTML 视图、登记表、锁定清单、安装与检查脚本。
- **其余各包只有二进制文件**：wheel、安装程序、外部工具压缩包。解压后，它们落到 01 已建好的目录里。

| 包 | 内容 | 何时需要 |
| --- | --- | --- |
| `…_01_docs_required` | 全部文本、HTML、脚本、锁定清单，以及 `tools/pip.pyz` | **必下** |
| `…_02_installers` | `installers/` 与两棵树的 `runtime/`（Python 3.10.11 / 3.12.10 / 3.13.17、VC++、Git） | **必下**（安装 Python 用） |
| `…_03` … `06_py310_part1..4` | `python310_amd64/environments/*/wheelhouse/` | 用 Python 3.10 时 |
| `…_07` … `10_py312_part1..4` | `python312_amd64/environments/*/wheelhouse/` | 用 Python 3.12 时 |
| `…_11_supplements_part1` | 3.10 定向补充包：wheel、源码包和外部工具（浏览器、驱动、FFmpeg、Tesseract） | 用 3.10 且需要这些补充时 |
| `…_12_supplements_part2` | 3.12 定向补充包，以及 3.10 / 3.12 的信号处理补充 | 用 3.12 或需要信号处理补充时 |
| `…_13_legacy` | `environments/*_py313` 试验目录；`project_specific/07b_gpflow_tf_py310`（与 3.10 树中的同名组相同） | 可选 |
| `…_14_caches` | 下载缓存 `supplement_cache/`、`supplement_signal_cache/`，内含 Linux aarch64 wheel 和源码包，**不是 Windows 安装用的**，只作来源留档 | 一般不需要 |

**典型下载组合**：只用 3.12 时，下载 01 + 02 + 07–10；需要补充包时再加 12。

各 part 包含哪些环境组，见 Release 说明或 `archive_index_cn.csv`。

## 解压

Windows 10/11 自带 `tar`，在 PowerShell 或 cmd 中都能用：

```powershell
mkdir D:\wpo
cd D:\wpo
tar -xf "$env:USERPROFILE\Downloads\windows_python_offline_r2_01_docs_required_cn_en.tar"
tar -xf "$env:USERPROFILE\Downloads\windows_python_offline_r2_02_installers_cn_en.tar"
# … 其余需要的包同样解压到 D:\wpo
```

- 解压顺序无所谓，各包之间没有同名文件。
- 也可以用 7-Zip 解压。
- 包内没有符号链接，也没有硬链接：同一个文件出现在多处时，每处都是完整副本。
- 中文文件名按 UTF-8 存储，Windows 自带 `tar` 和 7-Zip 都能正确还原。

## 离线阅读

用浏览器打开 `D:\wpo\index_cn.html`，不需要联网。

- 每个 Markdown 说明都有同名 `.html`，里面的路径都能点击，跳到本地文件或目录。
- 每个 CSV 登记表都有同名 `.html` 表格视图。
- 只有 http(s) 链接（上游来源）需要联网。
- 如果只下载了部分二进制包，指向未下载 wheel 的链接会打不开，这是正常的；说明页面本身都在 01 包里。

## 校验

`archive_index_cn.csv` 列出了每个文件所在的包、大小和 SHA256。在 PowerShell 中可以这样校验单个文件：

```powershell
Get-FileHash .\python312_amd64\runtime\python-3.12.10-amd64.exe -Algorithm SHA256
```

## 与资料库原件的差异

- **没有放入发布包的内容**：
  - 库根 `environments/` 下 30 个早期的 `*_py310` 副本：它们都是 `python310_amd64/environments/` 中同名组的子集。
  - `dist_supplement/`、`dist_supplement_signal/`：其中的 4 个 zip 已经单独发布为 Release `wpo-supplement-v1-20261030` 和 `wpo-supplement-signal-v1-20261030`，与本包中的 `*_supplement*` 目录逐文件相同。
- **修正**：有 3 处命令 `.\ .venv\Scripts\python.exe` 多了一个空格，已改为 `.\.venv\Scripts\python.exe`。
- **新增**：`.html` 视图和 `index_cn.html`；含中文的 CSV 加了 UTF-8 BOM。全部改动见 `offline_changes_cn.csv`。
- **未改动**：wheel、安装程序、外部工具和锁定清单。

## 安装

安装步骤见 `guides/windows_install_steps_cn.html`，补充包的用法见各 `*_supplement*/README_cn.html`。本库**只做了静态检查，没有在 Windows 上实际安装验证**。
