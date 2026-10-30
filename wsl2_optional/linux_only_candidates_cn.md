# 倾向 WSL2/Linux 的组件（登记，不下载）

| 组件 | 原因 | 建议 |
| --- | --- | --- |
| TensorFlow GPU ≥2.11 | 官方不再提供原生 Windows GPU | WSL2 + Linux GPU wheel |
| 无 win_amd64 的历史 sdist 包 | 需要编译器与系统库 | WSL2 或换有 wheel 的版本（不得擅自改项目要求） |
| MuJoCo / 部分 RL 仿真 | 体积大、许可证与二进制分发独立 | 需要时再单独取官方包 |
| Atari ROM | 法律与分发限制 | 不纳入通用库 |
| Stan/CmdStan 源码构建 | 需要 C++ 工具链 | 见 external_dependencies_cn.csv |
| JAX CUDA | 组合随 CUDA/驱动变化 | 有明确硬件后再锁 |

以上均未在本轮 Windows wheelhouse 中提供。
