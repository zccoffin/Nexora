# 🤖 Nexora Bot

**Boost your productivity with Nexora Bot – your friendly automation tool that handles key tasks with ease!**

[![Build Status](https://img.shields.io/badge/build-passed-brightgreen)](https://codeberg.org/livexords/ddai-bot/actions)
[![Telegram Group](https://img.shields.io/badge/Telegram-Join%20Group-2CA5E0?logo=telegram&style=flat)](https://t.me/livexordsscript)

---

## 🚀 About the Bot

Nexora Bot automates repetitive tasks so you can focus on what matters. Key features include:

- 📺 **Auto Watching Ads** – Earn rewards without manual effort  
- 💸 **Auto Withdraw** – Withdraw earnings directly to Binance UID  
- 👥 **Multi Account Support** – Manage multiple accounts easily  
- 🧵 **Thread System** – Run tasks concurrently for better performance  
- ⏱️ **Configurable Delays** – Customize timing between actions  
- 🔌 **Proxy Support** – Use HTTP/HTTPS proxies for multi-account setups

---

## 🌟 Version Updates

**Current Version: v1.0.0**

**New Features:**

- Auto watching ads  
- Auto withdraw  
- Multi-Account Support  
- Thread System  
- Configurable Delays  
- Proxy Support

---

## 📝 Register & Start Earning

Ready to automate and earn with Nexora Bot?  
Click below to register using our referral link and unlock full bot features! 🚀💸

👉 [**Register for Nexora Bot**](https://t.me/Nexora_UK_bot?startapp=6173601862)

---

## ⚙️ Configuration

### `config.json`

```json
{
  "address": "",
  "wd": true,
  "ads": true,
  "thread_ads": 5,
  "thread": 1,
  "proxy": false,
  "delay_account_switch": 10,
  "delay_loop": 3000
}
```

| Setting               | Description                                 | Default |
|----------------------|---------------------------------------------|---------|
| `address`            | Binance UID for withdrawals                 | `""`    |
| `wd`                 | Enable auto-withdraw                        | `true`  |
| `ads`                | Enable ad automation                        | `true`  |
| `thread_ads`         | Threads for ad watching                     | `5`     |
| `thread`             | Threads for general tasks                   | `1`     |
| `proxy`              | Enable proxy usage                          | `false` |
| `delay_account_switch` | Delay between account switches (sec)     | `10`    |
| `delay_loop`         | Delay before next loop (sec)                | `3000`  |

---

## 📦 Requirements

- Python 3.9+
- Required libraries:
  - colorama
  - requests
  - fake-useragent
  - brotli
  - chardet
  - urllib3

Install with:

```bash
pip install -r requirements.txt
```

---

## 🛠️ Installation Steps

```bash
git clone https://codeberg.org/LIVEXORDS/nexora-bot.git
cd nexora-bot
pip install -r requirements.txt
```

- Create `query.txt` and add your query data  
- (Optional) Create `proxy.txt` with proxies in format:  
  `http://username:password@ip:port`

Run the bot:

```bash
python main.py
```

---

## 🌐 Free Proxy Recommendation

Need proxies for farming or testnets?  
Get **1GB/month free** from [Webshare.io](https://www.webshare.io/?referral_code=k8udyiwp88n0) – no credit card, no KYC.

---

## 📁 Project Structure

```
nexora-bot/
├── config.json
├── query.txt
├── proxy.txt
├── main.py
├── requirements.txt
├── LICENSE
└── README.md
```

---



## 📖 License

Licensed under the **MIT License**.  
See the `LICENSE` file for details.

---

## 🔍 Usage Example

```bash
python main.py
```

Watch the bot start its operations. For help, join our Telegram group or open an issue.

---

## 📣 Community & Support

Join our Telegram group for updates, support, and feature requests.  
It’s the central hub for all things Nexora Bot!

---
```
