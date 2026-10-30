# 下载与解压说明（Windows 通用科研 Python 离线环境库）

本 Release 有 10 个 **不压缩 tar 包**（wheel 和安装程序本身已压缩，再压缩几乎不省空间）。所有包都解压到 **同一个目录**，例如 `D:\wpo\`。目录越短越好：最长相对路径 127 个字符，`D:\wpo\` 下不会超过 Windows 的 260 字符限制。

## 按需下载

| 包 | 内容 | 是否必需 |
| --- | --- | --- |
| `windows_python_offline_01_common_docs_installers_cn_en.tar` | 离线首页 `index_cn.html`、全部说明与登记表、`installers/`（Python 3.10/3.12/3.13、VC++、Git）、`tools/`、`state/` | **必下**（约 173 MiB） |
| `windows_python_offline_02` … `05_py310_part1..4` | 完整 3.10 树 `python310_amd64/`（part1 含 `runtime/`） | 用 Python 3.10 时 4 个都下 |
| `windows_python_offline_06` … `09_py312_part1..4` | 完整 3.12 树 `python312_amd64/`（part1 含 `runtime/`） | 用 Python 3.12 时 4 个都下 |
| `windows_python_offline_10_legacy_py313_project_specific_cn_en.tar` | `environments/*_py313` 试验目录，`project_specific/07b_gpflow_tf_py310`（与 3.10 树中同名组相同） | 可选 |

只用一个版本时，下载 01，再下载该版本的 4 个包。每个 part 只含完整的环境组，所以只想要某几组时也可以只下对应的 part，但 part1 带有该树的 `runtime/` 安装程序。各包里有哪些组，见 Release 说明或 `archive_index_cn.csv`。

## 解压

Windows 10/11 自带 `tar`（PowerShell 或 cmd 中都能用）：

```powershell
mkdir D:\wpo
cd D:\wpo
tar -xf "$env:USERPROFILE\Downloads\windows_python_offline_01_common_docs_installers_cn_en.tar"
tar -xf "$env:USERPROFILE\Downloads\windows_python_offline_06_py312_part1_cn_en.tar"
# … 其余 part 同样解压到 D:\wpo
```

7-Zip 也可以解压。包内没有符号链接，也没有硬链接：同一个 wheel 在多个环境组中各存一份完整文件，因此不同的解压工具得到的结果相同。

## 离线阅读

用浏览器打开 `D:\wpo\index_cn.html`，不需要联网。

- 每个 `README_cn.md` / 指南都有同名 `.html`，其中的路径都可以点击，跳到本地文件或目录。
- 每个 CSV 登记表都有同名 `.html` 表格视图：wheel 文件名可点击，直接定位到对应的 `.whl`。
- 原始 CSV 中，含中文的 4 个已加 UTF-8 BOM，用 Excel 双击打开不会乱码。
- 只有 http(s) 链接（上游来源）需要联网。

## 校验

`archive_index_cn.csv` 列出每个文件所在的包、大小和 SHA256。若要核对某个 wheel，可在 PowerShell 中执行：

```powershell
Get-FileHash .\python312_amd64\environments\01_base_scientific_py312\wheelhouse\numpy-*.whl -Algorithm SHA256
```

## 与原库的差异

- 库根 `environments/` 下的 30 个早期 `*_py310` 副本没有放入发布包。它们都是 `python310_amd64/environments/` 中同名组的子集，缺少后补的 Windows 标记依赖 wheel。请使用正式树。
- 66 个环境组说明中有一条命令 `.\ .venv\Scripts\python.exe` 多了一个空格，PowerShell 执行会报错。发布包中已改为 `.\.venv\Scripts\python.exe`。
- 新增了 `.html` 视图和 `index_cn.html`，并给 4 个 CSV 加了 BOM。全部改动见 `offline_changes_cn.csv`。
- wheel、安装程序和锁定清单都没有改动。

## 安装

安装步骤见 `guides/windows_install_steps_cn.html`。本库**只做了静态检查，没有在 Windows 上实际安装验证**。
