# Windows Python 3.10.11 信号处理定向补充

# 信号处理定向补充（Windows / Linux，Python 3.10 与 3.12）

本包是增量补充，**不覆盖**原 Release 资产，也不改原 `requirements_lock_en.txt`。
原 Windows 包：`wpo-full-20261030`；原 Linux 包：`lpo-full-20261030`。
Windows 上一轮工具补充仍是 `wpo-supplement-v1-20261030`，本包是另一份相关 Release。

## 覆盖范围

| 能力 | 包 | 说明 |
| --- | --- | --- |
| 傅里叶 / 频谱 | NumPy、SciPy | 已在原 **03 信号** 组，本包不重复下载 x86-64 / win_amd64 二进制 |
| 小波分解与重构 | PyWavelets | 同上，原 03 已有对应 CPython 版本的 wheel |
| EMD / EEMD / CEEMDAN | **EMD-signal** | pip 名 `EMD-signal`，**导入名 `PyEMD`** |
| Kalman 实时滤波 | filterpy | `predict` / `update`，因果 |
| Kalman 离线平滑 | pykalman | `filter` 因果；`smooth` 使用未来观测，仅离线 |

## 安装（在已有 03 环境上追加）

先按原树装好 `03_signal_*`（Windows 另可把 Linux 原 13 组里已有的 filterpy 视为无关，本包已带 Windows 可用的 any-wheel）。

Windows（PowerShell，已有 `.venv`）：

```powershell
powershell -ExecutionPolicy Bypass -File .\install_supplement_en.ps1
```

Linux：

```bash
bash ./install_supplement_en.sh
```

脚本只会安装 [`requirements_supplement_en.txt`](requirements_supplement_en.txt) 中的**新增**包，并从 [`packages_wheel/`](packages_wheel/) 以及原 03（及 Linux 原 13）wheelhouse 解析依赖。

必须使用对应树的 CPython **3.10.11 / 3.12.10**，不要装进 3.14。

## 实时滤波 vs 离线平滑

- **实时 / 因果**：`filterpy.kalman.KalmanFilter.predict` + `update`，或 `pykalman.KalmanFilter.filter`。时刻 t 的输出只依赖 `z[0]..z[t]`。
- **离线平滑**：`pykalman.KalmanFilter.smooth`（RTS）。时刻 t 的输出依赖 `z[0]..z[N-1]`，含未来观测。滞后更小、误差通常更低，**不能**接到必须在采样时刻给出估计的控制回路。

## 开发板

原库开发板侧是 Raspberry Pi OS Bookworm **Python 3.11** 的 GPIO 通讯包，**不是** 3.10/3.12。
本包不为 3.11 板子补信号库，也不把 **x86-64 / win_amd64** 二进制放进板端目录。
仅当存在 **aarch64 + 对应 CPython 3.10/3.12** 的 wheel 时，才写入 `embedded_boards/aarch64/`。
armv7l 若无官方 wheel，源码与构建依赖放在 [`packages_sdist_unbuilt/`](packages_sdist_unbuilt/)，状态为 **未构建、未验证**。

## 示例是否执行验证

[`examples/`](examples/) 下脚本仅作最小调用示意。本轮在下载主机上**未安装、未导入、未跑通**这些示例（状态：`未执行验证`）。

目标：Windows 10/11 x86-64，CPython 3.10.11。
NumPy / SciPy / PyWavelets 复用原 03 组已有兼容 wheel，见 [`reused_from_original_cn.csv`](reused_from_original_cn.csv) 仅记录本包实际硬链接到的文件。
本包新增主要是 EMD-signal（PyEMD）、filterpy、pykalman 及 pathos/scikit-base 等传递依赖。

