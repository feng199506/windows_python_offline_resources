# EMD / EEMD / CEEMDAN 分解与重构（EMD-signal，导入名 PyEMD）
# pip 包名：EMD-signal ；import：from PyEMD import EMD, EEMD, CEEMDAN
# 示例状态：未在目标机执行验证。

import numpy as np
from PyEMD import CEEMDAN, EEMD, EMD

t = np.linspace(0, 1, 400, endpoint=False)
x = np.sin(2 * np.pi * 6 * t) + 0.5 * np.sin(2 * np.pi * 25 * t)

emd = EMD()
imfs = emd(x)
recon = imfs.sum(axis=0)
print("emd_imfs", imfs.shape[0], "recon_mse", float(np.mean((recon - x) ** 2)))

# trials 取得很小，仅演示调用，不作为精度基准。
eemd = EEMD(trials=8, noise_width=0.05)
e_imfs = eemd(x)
print("eemd_imfs", e_imfs.shape[0])

ceemdan = CEEMDAN(trials=8)
c_imfs = ceemdan(x)
print("ceemdan_imfs", c_imfs.shape[0], "recon_mse", float(np.mean((c_imfs.sum(axis=0) - x) ** 2)))
