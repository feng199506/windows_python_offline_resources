# 小波分解、重构与去噪最小示例（PyWavelets）
# 依赖：原 03 组 PyWavelets / numpy。
# 示例状态：未在目标机执行验证。

import numpy as np
import pywt

rng = np.random.default_rng(0)
t = np.linspace(0, 1, 512, endpoint=False)
clean = np.sin(2 * np.pi * 8 * t)
noisy = clean + 0.4 * rng.normal(size=t.size)

wavelet = "db4"
coeffs = pywt.wavedec(noisy, wavelet, level=4)
recon_full = pywt.waverec(coeffs, wavelet)[: noisy.size]

# 软阈值去噪：只改细节系数，近似系数保持。
thr = 0.25 * np.median(np.abs(coeffs[-1])) / 0.6745
den = [coeffs[0]]
for c in coeffs[1:]:
    den.append(pywt.threshold(c, thr, mode="soft"))
denoised = pywt.waverec(den, wavelet)[: noisy.size]

print("recon_mse", float(np.mean((recon_full - noisy) ** 2)))
print("denoise_mse_vs_clean", float(np.mean((denoised - clean) ** 2)))
print("noisy_mse_vs_clean", float(np.mean((noisy - clean) ** 2)))
