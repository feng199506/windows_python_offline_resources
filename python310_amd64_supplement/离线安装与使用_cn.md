# 离线安装与使用

适用原 Release：**`wpo-full-20261030`**  
仓库：https://github.com/feng199506/windows_python_offline_resources/releases/tag/wpo-full-20261030

本文件随 **补充包** 发布，不修改原 Release 中的 tar 与锁定清单。  
**必须**用各树附带的 CPython **3.10.11** 或 **3.12.10** 创建环境。不能把这些 wheel / 源码直接装进 Python 3.14。

所有安装与调用示例均 **未在目标 Windows 上执行**（示例未验证）。

## 1. 原 Release 与补充包如何配合

1. 按 `download_restore_cn.md` 把原 tar 解压到同一目录，例如 `D:\wpo\`。
2. 将本补充 zip 解压到 **同一个目录**，得到：
   - `D:\wpo\python310_amd64\`（原树，不要改里面的 `requirements_lock_en.txt`）
   - `D:\wpo\python310_amd64_supplement\`（本轮新增）
   - 或对应的 `python312_amd64` / `python312_amd64_supplement`
3. 两棵树互相独立。只用 3.10 就下 3.10 的 4 个 part + 3.10 补充包；3.12 同理。
4. 外部工具（FFmpeg、Tesseract、浏览器）在 **两套补充目录里各有一份**，不要跨树共用路径。

## 2. 选择解释器

| 树 | 安装程序 | 建议路径 |
| --- | --- | --- |
| 3.10 | [`python310_amd64\runtime\python-3.10.11-amd64.exe`](../python310_amd64/runtime/python-3.10.11-amd64.exe) | `C:\Python310\python.exe` |
| 3.12 | [`python312_amd64\runtime\python-3.12.10-amd64.exe`](../python312_amd64/runtime/python-3.12.10-amd64.exe) | `C:\Python312\python.exe` |

同时安装 `runtime\vc_redist.x64.exe`。不要用 embeddable 包，不要用系统里的 3.14。

## 3. 创建原环境（锁定清单不变）

```powershell
cd D:\wpo\python312_amd64\environments\01_base_scientific_py312
powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1 -PythonExe "C:\Python312\python.exe"
.\.venv\Scripts\python.exe .\check_environment_en.py
```

脚本用 `--no-index --find-links wheelhouse` 安装 **该组** `requirements_lock_en.txt`。不要改这个 lock。

## 4. 安装补充清单（另行锁定）

补充可安装项在 [`requirements_supplement_en.txt`](requirements_supplement_en.txt)（wheel）和 [`requirements_supplement_sdist_en.txt`](requirements_supplement_sdist_en.txt)（源码，未构建）。

在 **已经装好的对应组 venv** 中追加，例如 3.10 量化组：

```powershell
cd D:\wpo\python310_amd64\environments\16_timeseries_quant_py310
$py = ".\.venv\Scripts\python.exe"
# 已有 Windows wheel 的补充项（akshare 1.18.88 等）
& $py -m pip install --no-index --find-links D:\wpo\python310_amd64_supplement\packages_wheel `
  -r D:\wpo\python310_amd64_supplement\requirements_supplement_en.txt
```

源码包（lime / ta / jieba / odfpy / jsonpath）**未构建、未验证**。仅在目标 Windows 上、且已安装 Visual C++ 运行库（纯 Python 包通常足够）时，才可以尝试：

```powershell
& $py -m pip install --no-index --find-links D:\wpo\python310_amd64_supplement\packages_sdist `
  --find-links .\wheelhouse `
  -r D:\wpo\python310_amd64_supplement\requirements_supplement_sdist_en.txt
```

不要把 Linux 上下载或构建的 wheel 拷进这些目录冒充 Windows 包。本轮 **没有** 在 Linux 上为这些包产出 win_amd64 wheel。

`lime` 还需要 `scikit-image`（在 03 组，不在 14 组）。未在 14 的 venv 中预装。

## 5. 外部工具调用

路径均相对于各套补充目录。把该目录加入 `PATH` 或在脚本里写绝对路径。

### FFmpeg（19_av_extra，以及需要命令行转码时）

解压 [`external\ffmpeg\ffmpeg-9.0.2-essentials_build.zip`](external/ffmpeg/ffmpeg-9.0.2-essentials_build.zip) 后：

```powershell
$env:Path = "D:\wpo\python312_amd64_supplement\external\ffmpeg\ffmpeg-9.0.2-essentials_build\bin;" + $env:Path
ffmpeg -version
```

`imageio-ffmpeg` / `ffmpeg-python` 只是封装；没有 `ffmpeg.exe` 时很多转码不能用。

### Tesseract（18_vision_extra / pytesseract）

1. 运行 [`external\tesseract\tesseract-ocr-w64-setup-5.4.0.20240606.exe`](external/tesseract/tesseract-ocr-w64-setup-5.4.0.20240606.exe)。
2. 将 [`external\tessdata\`](external/tessdata/) 下的 `eng.traineddata`、`chi_sim.traineddata`、`chi_tra.traineddata`、`osd.traineddata` 拷到 Tesseract 的 `tessdata` 目录，或设置：

```powershell
$env:TESSDATA_PREFIX = "D:\wpo\python312_amd64_supplement\external\tessdata"
```

3. Python 中（venv 已装 pytesseract）：

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

未在 Windows 上跑过，安装路径可能因选项而异。

### Selenium（22_crawler）

已提供 Chrome for Testing 156.0.8078.4 与匹配的 chromedriver，以及 geckodriver、msedgedriver。系统自带 Edge 时可用 msedgedriver；完整 Firefox 安装包未收录。

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
opt = Options()
opt.binary_location = r"D:\wpo\python312_amd64_supplement\external\chrome\chrome-win64\chrome.exe"
drv = webdriver.Chrome(
    service=Service(r"D:\wpo\python312_amd64_supplement\external\chromedriver\chromedriver-win64\chromedriver.exe"),
    options=opt,
)
```

先解压对应 zip。访问真实网站需要联网。

### Playwright（22b_playwright，playwright==1.64.1）

- Firefox rev 1555、WebKit rev 2370、Playwright 自带 ffmpeg rev 1013 已下载。
- 官方 Chromium rev 1248 的 `chromium-win64.zip` 在 CDN 上不可用（HTTP 400）。请用 Chrome for Testing 156.0.8078.4 作为 Chromium 可执行文件：

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=r"D:\wpo\python312_amd64_supplement\external\chrome\chrome-win64\chrome.exe"
    )
```

Firefox/WebKit 可解压到 Playwright 浏览器目录后设置 `PLAYWRIGHT_BROWSERS_PATH`（示例未验证）。

## 6. 不要做的事

- 不要覆盖原 `requirements_lock_en.txt`。
- 不要把 3.10 与 3.12 的包装进同一个 venv。
- 不要把本库装进 Python 3.14。
- 不要把 GPU / Linux wheel 混入 CPU 环境。
- 未下载：模型权重、NLTK/spaCy 语料、CUDA、数据库服务器、CmdStan 编译器、串口/烧录工具、完整 Firefox 安装包。
