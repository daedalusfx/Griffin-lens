# 🦅 Griffin-lens

##  فارسی

**موتور تحلیلی پیشرفته برای ارزیابی بی‌درنگ کیفیت کارگزاران در بازارهای مالی**  
*نسخه فارسی در این بخش – English below ⬇️*

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100-green?logo=fastapi&logoColor=white)
![Svelte](https://img.shields.io/badge/Svelte-4.0-orange?logo=svelte&logoColor=white)
![MQL5](https://img.shields.io/badge/MQL5-Expert-purple)
![License](https://img.shields.io/badge/License-GPLv3-blue)


![Logo](/screenshots/Griffin-lens.png)

![Preview](/screenshots/preview.png)






---

## معرفی

Griffin-lens یک پلتفرم تحلیل کیفیت فید قیمت از کارگزاران است. این سیستم داده‌های جمع‌آوری‌شده از MetaTrader 5 را تحلیل کرده و نتایج را از طریق یک داشبورد تعاملی نمایش می‌دهد.

**هدف:** کمک به معامله‌گران برای انتخاب کارگزاران مطمئن از طریق شفاف‌سازی کیفیت اجرای سفارش.

---

## ویژگی‌ها

- **امتیاز کیفیت (0 تا 100):** مقایسه سریع بین کارگزاران
- **تحلیل چندبُعدی:**  
  - اصالت داده (کشف داده مصنوعی)
  - یکپارچگی داده (شناسایی گلیچ و پرش قیمتی)
  - کیفیت اجرا (بررسی لغزش نامتقارن)
  - پایداری فید (تشخیص فریز یا قطعی)
  - تحلیل زمانی (میانگین امتیاز در بازه‌های مختلف)
- **داشبورد مدرن:** با Svelte و Tailwind
- **معماری ماژولار:** تفکیک لایه‌های جمع‌آوری، تحلیل و نمایش

---

## معماری سیستم

1. **اکسپرت MQL5:** جمع‌آوری داده‌های بازار
2. **سرور تحلیل (Python + FastAPI):** پردازش و امتیازدهی
3. **داشبورد (Svelte):** نمایش داده لحظه‌ای

---

## نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.8+
- Node.js 18+
- MetaTrader 5

### ۱. سرور تحلیل

```bash
git clone <your-repo-url>
cd griffin-backend
python -m venv venv
source venv/bin/activate  # ویندوز: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 5000 --reload
```

`requirements.txt` باید شامل موارد زیر باشد:

```
fastapi
uvicorn[standard]
numpy
pandas
scipy
```

### ۲. اکسپرت MQL5

- فایل `GriffinTickSender.mq5` را به مسیر `MQL5/Experts` منتقل کنید.
- در MetaTrader به `Tools > Options > Expert Advisors` رفته و `http://127.0.0.1:5000` را در WebRequest اضافه کنید.
- اکسپرت را به نمودار اضافه کرده و Algo Trading را فعال کنید.


---

## مجوز

این پروژه تحت مجوز **GPLv3** منتشر شده است. برای اطلاعات بیشتر به فایل `LICENSE` مراجعه کنید.

---


---

##  English

**An advanced analytical engine for real-time evaluation and monitoring of broker quality in financial markets**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100-green?logo=fastapi&logoColor=white)
![Svelte](https://img.shields.io/badge/Svelte-4.0-orange?logo=svelte&logoColor=white)
![MQL5](https://img.shields.io/badge/MQL5-Expert-purple)
![License](https://img.shields.io/badge/License-GPLv3-blue)

---

## Overview

Griffin-lens is a platform for evaluating the quality of market data feeds from brokers. It collects tick, slippage, and latency data from MetaTrader 5 and visualizes analysis results on a live dashboard.

**Goal:** Help traders choose reliable brokers by increasing transparency in execution quality.

---

## Features

- **Overall Quality Score (0–100):** For quick broker comparison
- **Multi-dimensional analysis:**  
  - Data Authenticity (detecting synthetic ticks)  
  - Data Integrity (glitch and jump detection)  
  - Execution Quality (asymmetric slippage)  
  - Feed Stability (freeze/disconnect detection)  
  - Timeframe Analysis (average score by time windows)
- **Modern Dashboard:** Built with Svelte and Tailwind
- **Modular Architecture:** Separation of data collection, analysis, and visualization

---

## System Architecture

1. **MQL5 Expert:** Sends tick/slippage/latency data
2. **Python FastAPI Server:** Processes, analyzes, and scores the data
3. **Svelte Dashboard:** Displays real-time analytics

---

## Installation

### Prerequisites

- Python 3.8+
- Node.js 18+
- MetaTrader 5

### 1. Backend Setup

```bash
git clone <your-repo-url>
cd griffin-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 5000 --reload
```

**requirements.txt:**

```
fastapi
uvicorn[standard]
numpy
pandas
scipy
```

### 2. MQL5 Expert Setup

- Copy `GriffinTickSender.mq5` to the `MQL5/Experts` folder in MetaTrader.
- Go to `Tools > Options > Expert Advisors` and enable WebRequest for `http://127.0.0.1:5000`.
- Attach the expert to a chart and enable Algo Trading.


## License

This project is licensed under the **GNU GPLv3**. See the `LICENSE` file for details.


---
