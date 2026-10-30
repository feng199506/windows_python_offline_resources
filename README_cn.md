# Windows 通用科研 Python 离线环境库

路径：`/root/windows_python_offline_resources/`

这是按用途准备的 **Windows 10/11 x86-64 离线基础环境**，不是已归档研究项目的精确复现。  
本轮只下载官方安装程序与 wheel，并做静态检查。 **未在目标 Windows 上安装，因此不能标记为安装验证通过。**

正式交付是两棵**互不依赖**的版本树：

| 树 | Python | 安装程序 | 环境组 | wheel 数 | 体积 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| [`python310_amd64/`](python310_amd64/) | **3.10.11** | `runtime/python-3.10.11-amd64.exe` | 31 | 1504 | 4.64 GiB | 旧代码兼容；3.10 已于 2026-10-01 EOL |
| [`python312_amd64/`](python312_amd64/) | **3.12.10** | `runtime/python-3.12.10-amd64.exe` | 31 | 1478 | 5.02 GiB | 仍受支持（至 2028-10）；最后带 Windows 安装程序的 3.12 |

每棵树自带 `runtime/`（Python + VC++）和完整 [`environments/`](environments/)。拷其中一棵到 Windows 即可，不必带另一棵。  
**不要**把 3.10 与 3.12 的 wheel 装进同一个 venv。

[`environments/`](environments/) 根下仍留有早期 py310 副本和少量 py313 试验目录，**不是**第二套正式树。正式树只用上面两个目录。

## 依赖范围（请按 lock 安装，不要只装名单上的包）

每一组都包含：

1. 该组的直接依赖（`requirements_direct_en.txt`）
2. pip 解析出的 **全部传递依赖**
3. 在 Linux 主机上按 Windows 环境标记补齐的包（例如 `colorama`、`pywin32`、`tomli`、`exceptiongroup`、`async-timeout`）

离线安装必须使用：

```powershell
python.exe -m pip install --no-index --find-links .\wheelhouse -r .\requirements_lock_en.txt
```

不要只用 `requirements_direct_en.txt`，否则会缺传递依赖。  
`wheelhouse/` 里是完整闭包；`.whl` 保持上游原始文件名。

## 安装程序（官方完整离线包）

目录：[`installers/`](installers/)（各树 `runtime/` 为硬链接副本）。明细见 [`installers/installer_inventory_cn.csv`](installers/installer_inventory_cn.csv)。

| 文件 | 版本 / 架构 | 大小 | 来源 | 校验 |
| --- | --- | --- | --- | --- |
| `python-3.10.11-amd64.exe` | 3.10.11 / x64 | 27.7 MiB | python.org FTP | SHA256 自算；页面仅公布 MD5 |
| `python-3.12.10-amd64.exe` | 3.12.10 / x64 | 25.7 MiB | python.org FTP | SHA256 `67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb`；MD5 与发布页一致 |
| `python-3.13.17-amd64.exe` | 3.13.17 / x64 | 28.6 MiB | python.org FTP | **遗留**，不属于正式两棵树 |
| `vc_redist.x64.exe` | VS 2015–2022 x64 | 24.4 MiB | aka.ms | Microsoft 签名 |
| `Git-2.56.0.4-64-bit.exe` | Git for Windows | 63.8 MiB | GitHub Release | SHA256 与 Release 一致 |

未使用 embeddable 包，未使用在线引导程序充当离线安装包。未下载 Python 3.14。

## 未下载的目标包（无 Windows wheel）

| 包 | 3.10 | 3.12 | 原因 |
| --- | --- | --- | --- |
| lime | 缺 | 缺 | 无 win_amd64 / any wheel |
| ta | 缺 | 缺 | 同上 |
| jieba | 缺 | 缺 | 同上 |
| odfpy | 缺 | 缺 | 同上 |
| akshare | 缺 | 已下 | 3.10 无兼容 wheel；3.12 有 |
| tensorflow-io-gcs-filesystem | 07b 已补 | 不需要 | TF 2.16 仅对 Python&lt;3.12 声明该依赖 |

其余冲突、外部工具见 [`compatibility_issues_cn.csv`](compatibility_issues_cn.csv)、[`external_dependencies_cn.csv`](external_dependencies_cn.csv)。

## 静态检查 vs Windows 运行验证

**已做：**

- 官方安装程序下载；SHA256 / MD5；PE Authenticode 证书表存在。
- `pip download --platform win_amd64 --python-version 310|312 --implementation cp --only-binary=:all:`，含传递依赖。
- 按 METADATA `Requires-Dist` 做 Windows 标记闭包。
- 每个 `.whl` 可 zip 打开；平台标签仅为 `win_amd64` 或纯 Python `any`。
- 无 CUDA torch、无 onnxruntime-gpu。

**未做（因此未验证安装）：**

- 未在 Windows 上建 venv、未 `pip install`、未 `import`、未训练。
- 未跑 `check_environment_en.py`。

## Windows 安装步骤

1. 拷贝 **一棵** 树到目标机：[`python310_amd64/`](python310_amd64/) 或 [`python312_amd64/`](python312_amd64/)。
2. 安装该树 `runtime/` 里的 Python 与 `vc_redist.x64.exe`（完整安装程序，不要用 embeddable）。
3. 进入某一组，例如：

```powershell
cd D:\python312_amd64\environments\01_base_scientific_py312
powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1 -PythonExe "C:\Python312\python.exe"
.\.venv\Scripts\python.exe .\check_environment_en.py
```

脚本用指定解释器新建 venv，`--no-index --find-links` 安装 **lock 中的全部包**，失败不会改去联网。

更细的步骤：[`guides/windows_install_steps_cn.md`](guides/windows_install_steps_cn.md)。版本政策：[`guides/python_version_policy_cn.md`](guides/python_version_policy_cn.md)。  
3.10 树说明：[`python310_amd64/README_cn.md`](python310_amd64/README_cn.md)。3.12 树说明：[`python312_amd64/README_cn.md`](python312_amd64/README_cn.md)。
