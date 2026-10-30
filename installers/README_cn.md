# 官方安装程序

全部保留上游原始文件名。完整离线安装程序，不是在线引导包，也不是 Python embeddable 包。

详细哈希与签名见 [`installer_inventory_cn.csv`](installer_inventory_cn.csv)。

## 选择依据

| 文件 | 用途 | 支持状态（截至 2026-10-30） |
| --- | --- | --- |
| python-3.10.11-amd64.exe | 正式树 [`python310_amd64/`](../python310_amd64/) | 3.10 已于 2026-10-01 EOL。这是最后带 Windows 安装程序的 3.10。 |
| python-3.12.10-amd64.exe | 正式树 [`python312_amd64/`](../python312_amd64/) | 3.12 安全支持至 2028-10。这是最后带 Windows 安装程序的 3.12；其后为源码安全修复。发布页 MD5 `5eddb0b6f12c852725de071ae681dde4` 已核对。 |
| python-3.13.17-amd64.exe | 遗留，非正式第二树 | 早期试验残留。 |
| vc_redist.x64.exe | MSVC 运行库 | 官方 standalone x64 redistributable。 |
| Git-2.56.0.4-64-bit.exe | Git for Windows | 官方 GitHub Release 完整安装程序。 |

未选用：

- Python 3.14/3.15：任务指定第二套为 3.12，不下载 3.14。
- embeddable zip：缺少完整开发/venv 体验，不用来替代常规安装程序。

## 数字签名（从 PE 证书表解析）

在 Linux 上确认 Authenticode 证书表存在，**未**用 Windows `signtool` 做信任链验证。

| 文件 | 说明 |
| --- | --- |
| python-3.10.11-amd64.exe | 证书表存在；主题需在 Windows 上用 signtool 查看 |
| python-3.12.10-amd64.exe | 证书表存在（size=14056）；另附官方 `.asc` / `.sigstore` |
| python-3.13.17-amd64.exe | 遗留；SHA256 与发布页一致 |
| vc_redist.x64.exe | Microsoft Corporation |
| Git-2.56.0.4-64-bit.exe | Johannes Schindelin；SHA256 与 GitHub Release 表一致 |

同时下载了 python.org 提供的 `.asc` 与 `.sigstore` 旁路文件。
