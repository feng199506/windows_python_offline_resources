# 常用工具与包用途索引

只解释 **直接目标包** 和你会主动调用的外部程序。传递依赖见各组 `requirements_lock_en.txt`，不在此写教程。  
Python 列为 3.10 与/或 3.12。不能装进 3.14。状态均为静态准备，**未在 Windows 上安装验证**。

图例：联网=运行该功能是否通常要访问网络；权重=是否还要模型/语料文件；外部=是否要补充包里的程序；硬件=是否依赖 GPU 等。

## 科学计算与 Notebook

| 名称 | 作用 | 适用场景 | 环境组 | Python | 联网 | 权重 | 外部 | 硬件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| numpy | 数组与线性代数 | 几乎所有数值代码 | 01 及多数组 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| scipy | 统计、优化、信号处理 | 科学计算 | 01、02、03、11 等 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| pandas | 表数据 | CSV/Excel 分析 | 01、16 等 | 3.10 / 3.12 | 读本地否；读 URL 是 | 否 | 否 | 否 |
| matplotlib / seaborn / plotly | 绘图 | 论文图、探索分析 | 01 | 3.10 / 3.12 | plotly 部分导出否 | 否 | 否 | 否 |
| jupyterlab | Notebook | 交互分析 | 01 | 3.10 / 3.12 | 装扩展时可能 | 否 | 否 | 否 |
| pyarrow / h5py / netCDF4 / xarray | 列存与科学数据格式 | 较大表格、气候/实验数据 | 01 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| sympy | 符号计算 | 公式推导 | 01 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |

## 传统机器学习 / 统计 / 解释性

| 名称 | 作用 | 适用场景 | 环境组 | Python | 联网 | 权重 | 外部 | 硬件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scikit-learn | 经典 ML | 分类回归聚类 | 02、14 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| statsmodels | 统计模型 | 回归、时间序列 | 02、16 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| xgboost / lightgbm / catboost | 提升树 | 表格竞赛/预测 | 02 | 3.10 / 3.12 | 否 | 否 | Graphviz 仅可视化 | 否 |
| hmmlearn | HMM | 序列/EM | 02 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| shap | 模型解释 | 特征贡献 | 14 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| lime | 局部解释 | 单样本解释 | 14 | 源码待构建 | 否 | 否 | 否 | 否 |
| imbalanced-learn / umap-learn / hdbscan | 不平衡、流形、密度聚类 | 14 组扩展 | 14 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |

## 深度学习（CPU）

| 名称 | 作用 | 适用场景 | 环境组 | Python | 联网 | 权重 | 外部 | 硬件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| torch / torchvision / torchaudio | PyTorch CPU | 小规模训练推理 | 04、05、08、09、15、17b | 3.10 / 3.12 | 下权重时 | 是（未提供） | 否 | GPU 未提供 |
| tensorflow-cpu / keras | TF CPU | 同上 | 07 | 3.10 / 3.12 | 下权重时 | 是（未提供） | 否 | 无原生 Windows GPU |
| gpflow | TF 路线 GPR | 与 07 的 TF 2.21 冲突，用 07b | 07b | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| gpytorch / botorch | PyTorch GPR/BO | 05 | 05 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| transformers / peft / datasets | Hugging Face 库 | LLM 微调与推理的**库** | 09 | 3.10 / 3.12 | 加载模型默认是 | 是（未提供） | 否 | CPU |
| sentence-transformers | 句向量 | 17b，与 17 分开 | 17b | 3.10 / 3.12 | 加载模型默认是 | 是（未提供） | 否 | CPU |
| onnxruntime | ONNX CPU 推理 | 10 | 10 | 3.10 / 3.12 | 否 | 模型文件自备 | 否 | 勿混 GPU 包 |
| lightning / timm / kornia | 训练框架与视觉组件 | 15 | 15 | 3.10 / 3.12 | timm 下预训练时 | 可能 | 否 | CPU |

## 时间序列与量化

| 名称 | 作用 | 适用场景 | 环境组 | Python | 联网 | 权重 | 外部 | 硬件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pmdarima / prophet / tsfresh | 时序建模与特征 | 16 | 16 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| yfinance | 行情 | 16 | 16 | 3.10 / 3.12 | **是** | 否 | 否 | 否 |
| akshare | 国内财经数据 | 16 | 16；3.10 见补充 1.18.88 | 3.10 补充 / 3.12 原锁 | **是** | 否 | 否 | 否 |
| backtrader | 回测 | 16 | 16 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| ta | 技术指标 | 16 | 源码待构建 | 否 | 否 | 否 | 否 |

## NLP / 文本

| 名称 | 作用 | 适用场景 | 环境组 | Python | 联网 | 权重 | 外部 | 硬件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nltk / spacy / gensim | 经典 NLP | 17 | 17 | 3.10 / 3.12 | download 语料时 | **语料未下** | 否 | 否 |
| jieba | 中文分词 | 17 | 源码待构建 | 否 | 否 | 否 | 否 |
| regex / lxml / textblob / wordcloud | 文本与词云 | 17 | 17 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |

## 图像 / 音频 / OCR / 视频

| 名称 | 作用 | 适用场景 | 环境组 | Python | 联网 | 权重 | 外部 | 硬件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| opencv-python-headless 4.10 | 图像 | 03 | 03 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| librosa / soundfile / mne | 音频与脑电 | 03 | 03 | 3.10 / 3.12 | 否 | 否 | 可选 FFmpeg | 否 |
| pytesseract | OCR 封装 | 18 | 18 | 3.10 / 3.12 | 否 | tessdata 已随补充 | **Tesseract** | 否 |
| Tesseract 5.4.0 | OCR 引擎 | 18 | 补充 external | n/a | 否 | eng/chi_sim/chi_tra/osd | 自身 | 否 |
| av / moviepy / pydub | 音视频 Python 层 | 19 | 19 | 3.10 / 3.12 | 否 | 否 | **FFmpeg** | 否 |
| FFmpeg 9.0.2 essentials | 转码 | 19 | 补充 external | n/a | 否 | 否 | 自身 | 否 |

## Web / 数据 / 爬虫 / 浏览器

| 名称 | 作用 | 适用场景 | 环境组 | Python | 联网 | 权重 | 外部 | 硬件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fastapi / gradio / streamlit | API 与小界面 | 10 | 10 | 3.10 / 3.12 | 服务对外时 | 否 | 否 | 否 |
| flask / django / celery | Web 扩展 | 20 | 20 | 3.10 / 3.12 | 视部署 | 否 | Redis 服务器未下 | 否 |
| sqlalchemy / duckdb / psycopg | 数据库客户端 | 21 | 21 | 3.10 / 3.12 | 连远程库时 | 否 | DB 服务器未下 | 否 |
| scrapy / selenium / bs4 | 爬虫 | 22 | 22 | 3.10 / 3.12 | **抓网页是** | 否 | Chrome/驱动 | 否 |
| Chrome for Testing 156.0.8078.4 | 浏览器 | 22 / 22b | 补充 | n/a | 访问站点时 | 否 | 自身 | 否 |
| chromedriver / geckodriver / msedgedriver | WebDriver | 22 | 补充 | n/a | 否 | 否 | 对应浏览器 | 否 |
| playwright 1.64.1 | 浏览器自动化 | 22b | 22b | 3.10 / 3.12 | 访问站点时 | 否 | Firefox/WebKit zip；Chromium 改用 Chrome | 否 |

## Office / GUI / 开发工具

| 名称 | 作用 | 适用场景 | 环境组 | Python | 联网 | 权重 | 外部 | 硬件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| python-docx / python-pptx / openpyxl / pypdf | 办公文档 | 23 | 23 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| odfpy | ODF | 23 | 源码待构建 | 否 | 否 | 否 | 否 |
| PyQt6 / PySide6 / wxPython / customtkinter | 桌面 GUI | 24* | 各 GUI 组勿混装 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |
| pytest / ruff / mypy / pyinstaller / sphinx | 测试与打包 | 25 | 25 | 3.10 / 3.12 | 否 | 否 | 否 | 否 |

## 优化、贝叶斯、强化学习

| 名称 | 作用 | 适用场景 | 环境组 | Python | 联网 | 权重 | 外部 | 硬件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cvxpy / casadi / python-control | 凸优化与控制 | 11 | 11 | 3.10 / 3.12 | 否 | 否 | 商业求解器未含 | 否 |
| pymc / arviz / emcee / cmdstanpy | 贝叶斯 | 06 | 06 | 3.10 / 3.12 | 否 | 否 | **CmdStan 本体未下** | 可选编译器 |
| gymnasium / stable-baselines3 | 经典控制 RL | 08 | 08 | 3.10 / 3.12 | 否 | 否 | 无 MuJoCo/Atari | CPU torch |

## 本轮补充包中的源码（未构建）

| 包 | 版本 | 拟用环境 | 说明 |
| --- | --- | --- | --- |
| lime | 0.2.0.1 | 14 | sdist；还需 scikit-image（03） |
| ta | 0.11.0 | 16 | sdist；依赖 pandas（16 已有） |
| jieba | 0.42.1 | 17 | sdist |
| odfpy | 1.4.1 | 23 | sdist；defusedxml 已在 23 |
| jsonpath | 0.82.2 | 16（akshare 依赖） | 无 win 二进制，仅 sdist |

## 未纳入（剩余缺口）

串口/烧录（pyserial、esptool 等）、CmdStan 工具链、CUDA、HF/spaCy/NLTK 数据、数据库服务器、完整 Firefox 安装包、Playwright 官方 Chromium rev 1248 zip、GTK/WeasyPrint、Java/tabula。
