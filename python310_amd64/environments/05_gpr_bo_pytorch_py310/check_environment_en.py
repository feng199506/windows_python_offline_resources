#!/usr/bin/env python3
"""Windows environment check for 05_gpr_bo_pytorch_py310. Run after offline install. Writes a local report without credentials."""
from __future__ import annotations

import importlib
import json
import platform
import struct
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_PY = (3, 10)
IMPORTS = ['numpy', 'torch', 'linear_operator', 'gpytorch', 'botorch']
GPU_ENV = False

def main() -> int:
    report = {
        "environment": "05_gpr_bo_pytorch_py310",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "executable": sys.executable,
        "python_version": sys.version,
        "version_info": list(sys.version_info),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "pointer_bits": struct.calcsize("P") * 8,
        "implementation": platform.python_implementation(),
        "ok": True,
        "errors": [],
        "imports": {},
        "pip_check": None,
        "ops": {},
        "gpu": {},
        "windows_install_verified": True,
        "note": "This flag is set only because this script ran on the target interpreter. Download hosts must not set it.",
    }
    errors = report["errors"]
    if sys.version_info[:2] != EXPECTED_PY:
        errors.append(f"expected Python {EXPECTED_PY}, got {sys.version_info[:2]}")
    if struct.calcsize("P") * 8 != 64:
        errors.append("expected 64-bit interpreter")
    if sys.platform != "win32":
        errors.append(f"expected win32, got {sys.platform}")

    try:
        import subprocess
        pip_chk = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True, text=True, check=False,
        )
        report["pip_check"] = {
            "returncode": pip_chk.returncode,
            "stdout": pip_chk.stdout.strip(),
            "stderr": pip_chk.stderr.strip(),
        }
        if pip_chk.returncode != 0:
            errors.append("pip check failed")
    except Exception as exc:
        errors.append(f"pip check error: {exc}")

    for name in IMPORTS:
        try:
            mod = importlib.import_module(name)
            report["imports"][name] = {
                "ok": True,
                "version": getattr(mod, "__version__", None),
            }
        except Exception:
            report["imports"][name] = {"ok": False, "error": traceback.format_exc()}
            errors.append(f"import failed: {name}")

    if "numpy" in report["imports"] and report["imports"]["numpy"]["ok"]:
        import numpy as np
        a = np.arange(9, dtype=np.float64).reshape(3, 3)
        b = a @ a.T
        report["ops"]["numpy_matmul_sum"] = float(b.sum())

    if "pandas" in report["imports"] and report["imports"].get("pandas", {}).get("ok"):
        import pandas as pd
        df = pd.DataFrame({"x": [1, 2, 3]})
        report["ops"]["pandas_sum"] = int(df["x"].sum())

    if "torch" in report["imports"] and report["imports"].get("torch", {}).get("ok"):
        import torch
        t = torch.ones(2, 2)
        report["ops"]["torch_sum"] = float(t.sum().item())
        report["gpu"]["torch_cuda_is_available"] = bool(torch.cuda.is_available())
        report["gpu"]["torch_version"] = torch.__version__
        if GPU_ENV and not torch.cuda.is_available():
            errors.append("GPU environment but torch.cuda.is_available() is False")

    if "tensorflow" in report["imports"] and report["imports"].get("tensorflow", {}).get("ok"):
        import tensorflow as tf
        x = tf.ones((2, 2))
        report["ops"]["tf_sum"] = float(tf.reduce_sum(x).numpy())
        report["gpu"]["tf_devices"] = [d.name for d in tf.config.list_physical_devices()]

    if "onnxruntime" in report["imports"] and report["imports"].get("onnxruntime", {}).get("ok"):
        import onnxruntime as ort
        report["gpu"]["ort_providers"] = ort.get_available_providers()

    report["ok"] = not errors
    out = Path(__file__).with_name("check_report_en.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    txt = Path(__file__).with_name("check_report_en.txt")
    lines = [
        f"environment={report['environment']}",
        f"ok={report['ok']}",
        f"python={report['python_version'].splitlines()[0]}",
        f"bits={report['pointer_bits']}",
        f"platform={report['platform']}",
        f"pip_check={report['pip_check']}",
        f"errors={errors}",
    ]
    txt.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print(txt.read_text(encoding="utf-8"))
    print(f"Wrote {out}")
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
