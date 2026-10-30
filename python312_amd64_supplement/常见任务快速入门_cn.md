# 常见任务快速入门

解释器必须是本库附带的 **Python 3.10.11** 或 **3.12.10**，不能用 3.14。  
下列示例按已下载版本编写，**未在 Windows 上执行（示例未验证）**。需要联网、权重或外部程序的已标明，不能当成开箱即用。

先按 [`离线安装与使用_cn.md`](%E7%A6%BB%E7%BA%BF%E5%AE%89%E8%A3%85%E4%B8%8E%E4%BD%BF%E7%94%A8_cn.md) 建好对应组的 venv。

## 数据分析（01_base_scientific）

已有：numpy、scipy、pandas、matplotlib、jupyterlab。不需要额外权重。Notebook 可离线打开，但拉取远程数据除外。

```python
import pandas as pd
df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
print(df.describe())
```

## 量化指标（16_timeseries_quant）

已有：pandas、statsmodels、pmdarima、prophet、yfinance、backtrader。  
`ta` 只有源码包，**未构建**。`akshare`：3.12 原 lock 已有 1.20.8；3.10 用补充包中的 **1.18.88** wheel（最新 1.20.x 要求 Python≥3.11）。

yfinance / akshare **默认要联网**。离线时只能用本地 CSV。

```python
import pandas as pd
s = pd.Series([1, 2, 3, 4, 5], dtype="float64")
print("pct_change", s.pct_change().dropna())
```

`ta` 若已在 Windows 上从补充 sdist 装好：

```python
import pandas as pd
from ta.momentum import RSIIndicator  # 需先成功安装 ta；示例未验证
df = pd.DataFrame({"close": [1, 2, 3, 4, 5]}, dtype="float64")
print(RSIIndicator(df["close"]).rsi())
```

## 机器学习（02_ml_stats / 14_ml_extra）

02：scikit-learn、xgboost 2.0.3、lightgbm、catboost、hmmlearn。CPU，无 CUDA。  
14：imbalanced-learn、shap、umap、hdbscan。`lime` 仅 sdist，未构建；且 lime 依赖 `scikit-image`（在 03 组）。

```python
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import load_iris
X, y = load_iris(return_X_y=True)
m = LogisticRegression(max_iter=200)
m.fit(X, y)
print(m.score(X, y))
```

解释性：优先用已有 **shap**。lime 未验证。

## 中文处理（17_nlp_classic）

已有：nltk、spacy、gensim、regex。`jieba` 仅 sdist，未构建。  
**未下载** spaCy 模型与 NLTK 语料，`nltk.download` / `spacy.load("en_core_web_sm")` 在离线机上会失败。

在 jieba 于 Windows 上从 sdist 安装成功之前，不要假定中文分词可用。装好后：

```python
import jieba  # 需补充源码安装成功；示例未验证
print(list(jieba.cut("中文分词示例")))
```

句向量见 17b（sentence-transformers），**不含权重**，第一次 `from_pretrained` 要联网或自备模型目录。

## PDF / Office（23_office_pdf）

已有：python-docx、python-pptx、openpyxl、pypdf、pdfplumber、reportlab。`odfpy` 仅 sdist，未构建。  
未含 WeasyPrint/GTK、tabula/Java、camelot/Ghostscript。

```python
from pypdf import PdfReader
reader = PdfReader("local.pdf")  # 需要你自己的 PDF 文件
print(len(reader.pages))
```

## 音视频（19_av_extra + 补充 FFmpeg）

已有：av、moviepy、pydub、mutagen。命令行 **FFmpeg 9.0.2 essentials** 在补充包 [`external/ffmpeg/`](external/ffmpeg/)。  
没有 FFmpeg 时，封装库不能完成多数转码。处理本地文件可离线。

```powershell
ffmpeg -i input.mp4 -vn -acodec copy out.aac
```

## OCR（18_vision_extra + 补充 Tesseract）

已有：pytesseract、Pillow。必须安装 Tesseract 安装程序，并配置 `chi_sim` / `eng` 等 traineddata。  
**不是**开箱即用。

```python
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# img = Image.open("scan.png")
# print(pytesseract.image_to_string(img, lang="chi_sim+eng"))
```

## 浏览器自动化（22_crawler / 22b_playwright）

Selenium 4.52 + Chrome for Testing 156.0.8078.4 + chromedriver 已提供。  
Playwright 1.64.1：Firefox/WebKit 已下；官方 Chromium zip 缺失，改用上述 Chrome。  
访问互联网 **需要联网**。未提供完整 Firefox 安装包；系统 Edge 可用 msedgedriver。

见 [`离线安装与使用_cn.md`](%E7%A6%BB%E7%BA%BF%E5%AE%89%E8%A3%85%E4%B8%8E%E4%BD%BF%E7%94%A8_cn.md) 中的启动示例。

## 串口及开发板通信

本 Windows 31 组 **未纳入** `pyserial`、`esptool` 等包，也 **未下载** 烧录器、交叉编译器或板卡镜像。  
该项为剩余缺口，没有可运行示例。不要把 Linux 段的嵌入式工具当成已随本 Windows 库提供。

## 深度学习推理（04 / 07 / 09，提醒）

torch / tensorflow-cpu 已在对应组。**权重未下载**。`transformers` 加载模型默认联网。CPU only，无 CUDA。
