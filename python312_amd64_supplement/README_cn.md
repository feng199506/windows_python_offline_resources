# Python 3.12.10 定向补充包 v1

适用原 Release 标签：**`wpo-full-20261030`**  
https://github.com/feng199506/windows_python_offline_resources/releases/tag/wpo-full-20261030

## 解压位置

与原 tar **解压到同一目录**（例如 `D:\wpo\`），得到与 [`python312_amd64\`](../python312_amd64/) 并列的 [`python312_amd64_supplement\`](./)。  
不要覆盖原树中的 `requirements_lock_en.txt` 和 wheelhouse。

## 使用方法

见 [`离线安装与使用_cn.md`](%E7%A6%BB%E7%BA%BF%E5%AE%89%E8%A3%85%E4%B8%8E%E4%BD%BF%E7%94%A8_cn.md)。索引见 [`常用工具与包用途索引_cn.md`](%E5%B8%B8%E7%94%A8%E5%B7%A5%E5%85%B7%E4%B8%8E%E5%8C%85%E7%94%A8%E9%80%94%E7%B4%A2%E5%BC%95_cn.md)。任务示例见 [`常见任务快速入门_cn.md`](%E5%B8%B8%E8%A7%81%E4%BB%BB%E5%8A%A1%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8_cn.md)。

必须使用 [`python312_amd64\runtime\python-3.12.10-amd64.exe`](../python312_amd64/runtime/python-3.12.10-amd64.exe)，不能装进 Python 3.14。

## 本包内容摘要

- [`packages_sdist/`](packages_sdist/)：lime、ta、jieba、odfpy、jsonpath 源码。**未构建、未验证。**
- [`packages_wheel/`](packages_wheel/)：仅本轮新增、可用于 Windows 的 wheel（3.10 含 akshare 1.18.88 等）。3.12 的 akshare 已在原 lock。
- [`external/`](external/)：浏览器、驱动、FFmpeg、Tesseract 与语言数据。
- 原 lock 不变；新项见 [`requirements_supplement_en.txt`](requirements_supplement_en.txt) 与 [`requirements_supplement_sdist_en.txt`](requirements_supplement_sdist_en.txt)。
