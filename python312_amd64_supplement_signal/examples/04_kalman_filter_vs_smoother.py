# Kalman：实时滤波 vs 使用未来观测的离线平滑
#
# filterpy：逐步 predict/update，只使用截至当前时刻的观测 → 实时 / 因果滤波。
# pykalman.smooth：RTS 平滑，使用整段未来观测 → 离线非因果，不能当实时输出。
#
# 示例状态：未在目标机执行验证。

import numpy as np
from filterpy.kalman import KalmanFilter
from pykalman import KalmanFilter as PKKalman

rng = np.random.default_rng(1)
n = 80
truth = np.cumsum(0.2 + 0.05 * rng.normal(size=n))
z = truth + 0.4 * rng.normal(size=n)

# --- 实时滤波（filterpy）---
kf = KalmanFilter(dim_x=2, dim_z=1)
kf.x = np.array([[z[0]], [0.0]])
kf.F = np.array([[1.0, 1.0], [0.0, 1.0]])
kf.H = np.array([[1.0, 0.0]])
kf.P *= 10.0
kf.R *= 0.16
kf.Q = np.array([[0.01, 0.0], [0.0, 0.01]])
online = []
for zi in z:
    kf.predict()          # 只用过去状态
    kf.update(zi)         # 只用当前观测，不用未来
    online.append(float(kf.x[0, 0]))
online = np.asarray(online)

# --- 离线平滑（pykalman RTS）---
pk = PKKalman(
    transition_matrices=[[1, 1], [0, 1]],
    observation_matrices=[[1, 0]],
    initial_state_mean=[z[0], 0],
)
filt_mean, _ = pk.filter(z)     # 因果滤波（可用实时）
smooth_mean, _ = pk.smooth(z)   # 使用 t..N 的观测，只能离线

print("online_mse", float(np.mean((online - truth) ** 2)))
print("filter_mse", float(np.mean((filt_mean[:, 0] - truth) ** 2)))
print("smooth_mse", float(np.mean((smooth_mean[:, 0] - truth) ** 2)))
print("note: smooth_mse 通常更小，因为它看到了未来观测，不能用于实时控制回路")
