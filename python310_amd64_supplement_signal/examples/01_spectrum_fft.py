# 傅里叶与频谱分析最小示例（NumPy / SciPy）
# 依赖：原 03 组 numpy、scipy。本补充包不重复打包这两项。
# 示例状态：未在目标机执行验证。

import numpy as np
from scipy import signal
from numpy.fft import rfft, rfftfreq

fs = 500.0
t = np.arange(0, 2, 1 / fs)
x = np.sin(2 * np.pi * 20 * t) + 0.4 * np.sin(2 * np.pi * 80 * t)

freqs = rfftfreq(x.size, 1 / fs)
spec = np.abs(rfft(x))
peak = freqs[int(np.argmax(spec[1:])) + 1]

f_welch, pxx = signal.welch(x, fs=fs, nperseg=256)
print("fft_peak_hz", round(float(peak), 3))
print("welch_peak_hz", round(float(f_welch[int(np.argmax(pxx))]), 3))
