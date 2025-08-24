from datetime import datetime, timezone, timedelta
import threading
import time
from typing import Any
from urllib.parse import parse_qs, unquote
from colorama import Fore, init as colorama_init
import requests
import random
from fake_useragent import UserAgent
import asyncio
import json
import gzip
import brotli
import zlib
import chardet
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from queue import Queue


# Initialize colorama once for cross-platform color support
colorama_init(autoreset=True)


class ProxyManager:
    def __init__(self, proxy_list: list[str]):
        self.proxy_pool = Queue()
        for p in proxy_list:
            self.proxy_pool.put(p)

    def get_proxy(self) -> str | None:
        if not self.proxy_pool.empty():
            return self.proxy_pool.get()
        return None

    def release_proxy(self, proxy: str):
        self.proxy_pool.put(proxy)


class nexora:
    BASE_URL = "https://instatasker.online/"
    HEADERS = {
        "accept": "*/*",
        "accept-encoding": "br",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://instatasker.online",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://instatasker.online/",
        "sec-ch-ua": '"Chromium";v="139", "Microsoft Edge WebView2";v="139", "Microsoft Edge";v="139", "Not;A=Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
    }

    def __init__(self, use_proxy: bool = False, proxy_list: list = None):
        self.config = self.load_config()
        self.query_list = self.load_query("query.txt")
        self.telegramid = None
        self.coin = 0
        self.payment_method = None
        self.proxy_list = proxy_list or self.load_proxies()
        self.proxy_manager = ProxyManager(self.proxy_list) if self.config.get("proxy") else None
        self.session = None
        self.proxy = None

    # ---------- UI ----------
    def banner(self) -> None:
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Fore.LIGHTBLACK_EX)
        self.log("✨ Nexora Bot", Fore.CYAN)
        self.log("🚀 Created by LIVEXORDS", Fore.CYAN)
        self.log("📢 Channel: t.me/livexordsscript", Fore.CYAN)
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", Fore.LIGHTBLACK_EX)

    def log(self, message, color=Fore.RESET):
        safe_message = str(message).encode("utf-8", "backslashreplace").decode("utf-8")
        print(
            Fore.LIGHTBLACK_EX
            + datetime.now().strftime("[%Y:%m:%d ~ %H:%M:%S] |")
            + " "
            + color
            + safe_message
            + Fore.RESET
        )

    # ---------- Helpers ----------
    def _fmt_duration(self, seconds: int) -> str:
        seconds = max(0, int(seconds))
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m}m {s}s"

    def _progress_bar(self, current: int, total: int) -> str:
        total = max(1, int(total))
        current = max(0, min(int(current), total))
        width = int(self.config.get("progress_bar_width", 20))
        filled = int((current / total) * width)
        return "█" * filled + "░" * (width - filled)

    def _seconds_until_reset(self) -> int:
        reset_str = str(self.config.get("reset_time", "00:00"))
        tz = str(self.config.get("reset_timezone", "local")).lower()

        try:
            hh, mm = [int(x) for x in reset_str.split(":", 1)]
        except Exception:
            hh, mm = 0, 0

        if tz == "utc":
            now = datetime.now(timezone.utc)
            today_reset = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        else:
            now = datetime.now()
            today_reset = now.replace(hour=hh, minute=mm, second=0, microsecond=0)

        if now >= today_reset:
            next_reset = today_reset + timedelta(days=1)
        else:
            next_reset = today_reset

        return int((next_reset - now).total_seconds())

    def _wait_until_reset_blocking(self):
        wait_secs = self._seconds_until_reset()
        if wait_secs <= 0:
            return

        self.log(
            f"😴 Daily limit reached. Waiting until next reset in {self._fmt_duration(wait_secs)}...",
            Fore.MAGENTA,
        )
        while wait_secs > 0:
            chunk = min(300, wait_secs)
            time.sleep(chunk)
            wait_secs -= chunk
        self.log("🌅 New day detected. Resuming tasks.", Fore.GREEN)

    def decode_response(self, response: Any) -> Any:
        if isinstance(response, str):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return response

        content_encoding = response.headers.get("Content-Encoding", "").lower()
        data = response.content

        try:
            if content_encoding == "gzip":
                data = gzip.decompress(data)
            elif content_encoding in ["br", "brotli"]:
                data = brotli.decompress(data)
            elif content_encoding in ["deflate", "zlib"]:
                data = zlib.decompress(data)
        except Exception:
            pass

        content_type = response.headers.get("Content-Type", "").lower()
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip()

        try:
            text = data.decode(charset)
        except Exception:
            detected = chardet.detect(data)
            text = data.decode(detected.get("encoding", "utf-8"), errors="replace")

        stripped = text.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                pass

        return text

    # ---------- IO ----------
    def load_config(self) -> dict:
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
                self.log("✅ Configuration loaded successfully.", Fore.GREEN)
                return cfg
        except FileNotFoundError:
            self.log("❌ File not found: config.json", Fore.RED)
            return {}
        except json.JSONDecodeError:
            self.log("❌ Failed to parse config.json. Please check the file format.", Fore.RED)
            return {}

    def load_query(self, path_file: str = "query.txt") -> list:
        try:
            with open(path_file, "r", encoding="utf-8") as f:
                queries = [line.strip() for line in f if line.strip()]
            if not queries:
                self.log(f"⚠️ Warning: {path_file} is empty.", Fore.YELLOW)
            self.log(f"✅ Loaded {len(queries)} queries from {path_file}.", Fore.GREEN)
            return queries
        except FileNotFoundError:
            self.log(f"❌ File not found: {path_file}", Fore.RED)
            return []
        except Exception as e:
            self.log(f"❌ Unexpected error loading queries: {e}", Fore.RED)
            return []

    def load_proxies(self, filename="proxy.txt"):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                proxies = list(set([line.strip() for line in file if line.strip()]))
            if not proxies:
                raise ValueError("Proxy file is empty.")
            return proxies
        except Exception as e:
            self.log(f"❌ Failed to load proxies: {e}", Fore.RED)
            return []

    # ---------- Networking ----------
    def prepare_session(self) -> None:
        class TimeoutHTTPAdapter(HTTPAdapter):
            def __init__(self, *args, **kwargs):
                self.timeout = kwargs.pop("timeout", 10)
                super().__init__(*args, **kwargs)
            def send(self, request, **kwargs):
                kwargs["timeout"] = kwargs.get("timeout", self.timeout)
                return super().send(request, **kwargs)

        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            raise_on_status=False,
        )
        adapter = TimeoutHTTPAdapter(max_retries=retries, timeout=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            ua = UserAgent()
            headers = {**self.HEADERS, "User-Agent": ua.random}
            session.headers.update(headers)
        except Exception as e:
            self.log(f"⚠️ Failed to set random User-Agent: {e}", Fore.YELLOW)
            session.headers.update(self.HEADERS)

        self.proxy = None
        if self.config.get("proxy") and self.proxy_manager:
            result = {"proxy": None}
            def test_proxy(proxy: str):
                if result["proxy"]:
                    return
                test_sess = requests.Session()
                test_sess.headers.update(session.headers)
                test_sess.proxies = {"http": proxy, "https": proxy}
                try:
                    resp = test_sess.get("https://httpbin.org/ip", timeout=5)
                    resp.raise_for_status()
                    ip = resp.json().get("origin", "Unknown")
                    if not result["proxy"]:
                        result["proxy"] = proxy
                        self.log(f"✅ Proxy connected: {proxy} | IP: {ip}", Fore.GREEN)
                        time.sleep(0.5)
                except Exception:
                    pass

            threads = []
            shuffled_proxies = self.proxy_list[:]
            random.shuffle(shuffled_proxies)
            for proxy in shuffled_proxies:
                t = threading.Thread(target=test_proxy, args=(proxy,))
                t.start()
                threads.append(t)
                # test a few at a time
                if len(threads) >= 4:
                    for th in threads:
                        th.join()
                    threads = []
                if result["proxy"]:
                    break
            for th in threads:
                th.join()

            if result["proxy"]:
                session.proxies = {"http": result["proxy"], "https": result["proxy"]}
                self.proxy = result["proxy"]
            else:
                self.log("⚠️ No working proxy found, fallback to local.", Fore.YELLOW)
                session.proxies = {}
        else:
            session.proxies = {}
            self.log("🌐 Using local IP connection (no proxy).", Fore.YELLOW)

        self.session = session

    # ---------- Core flows ----------
    def login(self, index: int) -> None:
        if index < 0 or index >= len(self.query_list):
            self.log("❌ Invalid login index. Please verify the index.", Fore.RED)
            return

        self.prepare_session()
        raw_qs = self.query_list[index].strip()

        try:
            resp = self.session.get(self.BASE_URL, headers=self.HEADERS)
            resp.raise_for_status()

            # Extract CSRF token
            csrf_token = None
            if "X-CSRF-TOKEN" in resp.text:
                import re
                match = re.search(r'X-CSRF-TOKEN":\s*"(.+?)"', resp.text)
                if match:
                    csrf_token = match.group(1)

            if not csrf_token:
                self.log("❌ CSRF token not found in page.", Fore.RED)
                return
            self.HEADERS["X-CSRF-TOKEN"] = csrf_token

            # Cookies
            cookies = resp.cookies
            xsrf = cookies.get("XSRF-TOKEN")
            laravel = cookies.get("laravel_session")
            if not xsrf or not laravel:
                self.log("❌ Required cookies not found.", Fore.RED)
                return
            self.HEADERS["cookie"] = f"XSRF-TOKEN={xsrf}; laravel_session={laravel}"

            # Payment method
            import re
            payment_match = re.search(
                r'<div class="d-flex gap-2 flex-wrap" id="payment-method-buttons">.*?data-id="(\d+)"',
                resp.text,
                re.DOTALL,
            )
            if payment_match:
                self.payment_method = int(payment_match.group(1))
                self.log(f"💳 Payment method ID found: {self.payment_method}", Fore.CYAN)
            else:
                self.log("❌ Payment method ID not found.", Fore.RED)
                return

        except Exception as e:
            self.log(f"❌ Error fetching BASE_URL: {e}", Fore.RED)
            return

        # Parse telegram user from query string
        parsed = parse_qs(unquote(raw_qs))
        user_data = {}
        if "user" in parsed:
            user_str = parsed["user"][0].replace(r"\/", "/")
            try:
                user_data = json.loads(user_str)
            except Exception as e:
                self.log(f"❌ Failed parsing user data: {e}", Fore.RED)
                return
        else:
            self.log("❌ Telegram user data not found in query.", Fore.RED)
            return

        payload = {
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "username": user_data.get("username", ""),
            "language_code": user_data.get("language_code", ""),
            "photo_url": user_data.get("photo_url", ""),
            "is_premium": user_data.get("is_premium", False),
            "id": user_data.get("id"),
            "referral_code": None,
        }

        try:
            url = self.BASE_URL + "user/check-or-create"
            resp = self.session.post(url, headers=self.HEADERS, json=payload)
            resp.raise_for_status()
            data = resp.json()

            if data.get("success"):
                u = data.get("user", {})
                self.telegramid = u.get("telegram_id")
                self.coin = u.get("balance", 0)
                self.log("✅✨ User data fetched!", Fore.GREEN)
                self.log(f"🆔 ID: {u.get('id')} 🌟", Fore.CYAN)
                self.log(f"📲 Telegram ID: {u.get('telegram_id')} 💬", Fore.CYAN)
                self.log(f"👤 Username: {u.get('username')} 😎", Fore.CYAN)
                self.log(f"📝 Name: {u.get('first_name')} {u.get('last_name')} 🐾", Fore.CYAN)
                self.log(f"🖼️ Photo URL: {u.get('photo_url')} 📸", Fore.CYAN)
                self.log(f"💰 Balance: {u.get('balance')} 🤑", Fore.CYAN)
            else:
                self.log("❌ Failed to create/check user.", Fore.RED)

        except Exception as e:
            self.log(f"❌ Error during POST user/check-or-create: {e}", Fore.RED)

    def ads(self) -> dict:
        result = {
            "success": False,
            "reached_limit": False,
            "today_ads": 0,
            "ads_limit": 0,
            "new_balance": self.coin,
        }

        if not self.telegramid:
            self.log("❌ Not logged in. Call login() first.", Fore.RED)
            return result

        url = self.BASE_URL + "user/reward"
        thread_count = int(self.config.get("thread_ads", 1))
        human_delay = self.config.get("human_delay", [1.5, 3.0])
        min_delay = float(human_delay[0]) if isinstance(human_delay, (list, tuple)) and len(human_delay) >= 1 else 1.0
        max_delay = float(human_delay[1]) if isinstance(human_delay, (list, tuple)) and len(human_delay) >= 2 else min_delay + 1.0

        stop_event = threading.Event()
        state_lock = threading.Lock()

        def log_progress(tid, today, limit, balance):
            bar = self._progress_bar(today, max(1, limit))
            self.log(f"📺 T{tid} | [{bar}] {today}/{limit} | 🪙 {balance}", Fore.CYAN)

        def watch_ads_thread(thread_id: int):
            self.log(f"🎬 Thread-{thread_id} started.", Fore.MAGENTA)
            while not stop_event.is_set():
                try:
                    payload = {"telegram_id": self.telegramid}
                    resp = self.session.post(url, headers=self.HEADERS, json=payload)
                    resp.raise_for_status()
                    data = resp.json()

                    if not isinstance(data, dict):
                        self.log(f"⚠️ T{thread_id}: Unexpected response type.", Fore.YELLOW)
                        break

                    if not data.get("success"):
                        message = data.get("message", "No more ads or server error.")
                        self.log(f"⚠️ T{thread_id}: {message}", Fore.YELLOW)
                        stop_event.set()
                        break

                    today_ads = int(data.get("today_ads", 0))
                    ads_limit = int(data.get("ads_limit", 0))
                    new_balance = int(data.get("new_balance", self.coin))

                    with state_lock:
                        result["success"] = True
                        result["today_ads"] = today_ads
                        result["ads_limit"] = ads_limit
                        result["new_balance"] = new_balance
                        self.coin = new_balance

                    log_progress(thread_id, today_ads, ads_limit, new_balance)

                    if ads_limit and today_ads >= ads_limit:
                        self.log(
                            f"✅ T{thread_id}: Reached daily ads limit ({today_ads}/{ads_limit}) 🎉",
                            Fore.GREEN,
                        )
                        result["reached_limit"] = True
                        stop_event.set()
                        break

                    time.sleep(random.uniform(min_delay, max_delay))

                except Exception as e:
                    self.log(f"❌ T{thread_id}: Error while watching ads: {e}", Fore.RED)
                    break

            self.log(f"🛑 Thread-{thread_id} finished.", Fore.LIGHTBLACK_EX)

        threads = []
        for i in range(max(1, thread_count)):
            t = threading.Thread(target=watch_ads_thread, args=(i + 1,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        if result["ads_limit"]:
            bar = self._progress_bar(result["today_ads"], result["ads_limit"])
            self.log(
                f"🎉 Ads session done: [{bar}] {result['today_ads']}/{result['ads_limit']} | 🪙 {result['new_balance']}",
                Fore.MAGENTA,
            )
        else:
            self.log("🎉 Ads session finished.", Fore.MAGENTA)

        return result

    def run_ads_daily(self):
        auto_next = bool(self.config.get("auto_next_day", True))
        while True:
            out = self.ads()
            if out.get("reached_limit") and auto_next:
                self._wait_until_reset_blocking()
                continue
            break

    def wd(self) -> None:
        url = self.BASE_URL + "user/withdraw"
        payload = {
            "telegram_id": self.telegramid,
            "amount": self.coin,
            "payment_method_id": self.payment_method,
            "address": self.config.get("address"),
        }

        try:
            resp = self.session.post(url, headers=self.HEADERS, json=payload)
            resp.raise_for_status()
            data = resp.json()

            if data.get("success"):
                self.log(f"✅ Withdrawal successful! 💸 Amount: {self.coin}", Fore.GREEN)
                self.log(f"📬 Sent to address: {self.config.get('address')}", Fore.CYAN)
            else:
                message = data.get("message", "Unknown error occurred.")
                self.log(f"⚠️ Withdrawal failed: {message}", Fore.YELLOW)

        except Exception as e:
            self.log(f"❌ Error during withdrawal: {e}", Fore.RED)


# ---------- Account runner ----------
async def process_account(account, original_index, account_label, blu, cfg_snapshot):
    cfg_snapshot = blu.load_config()
    display_account = account[:10] + "..." if len(account) > 10 else account
    blu.log(f"👤 Processing {account_label}: {display_account}", Fore.YELLOW)

    await asyncio.to_thread(blu.login, original_index)

    blu.log("🛠️ Starting task execution...", Fore.CYAN)
    tasks_config = {"ads": "Auto watching ads", "wd": "Auto withdraw"}
    for task_key, task_name in tasks_config.items():
        task_status = cfg_snapshot.get(task_key, False)
        color = Fore.YELLOW if task_status else Fore.RED
        blu.log(f"[CONFIG] {task_name}: {'✅ Enabled' if task_status else '❌ Disabled'}", color)

    if cfg_snapshot.get("ads", False):
        blu.log("🔄 Executing Auto watching ads...", Fore.CYAN)
        await asyncio.to_thread(blu.run_ads_daily)

    if cfg_snapshot.get("wd", False):
        blu.log("💸 Executing Auto withdraw...", Fore.CYAN)
        await asyncio.to_thread(blu.wd)

    blu.log("✅ Task execution complete for this account.", Fore.GREEN)


async def main():
    bot = nexora()
    bot.banner()

    if not bot.query_list:
        bot.log("⚠️ No accounts in query.txt. Add at least one.", Fore.YELLOW)
        return

    max_concurrent = int(bot.config.get("max_concurrent", 2))
    sem = asyncio.Semaphore(max_concurrent)

    async def run_one(i, q):
        async with sem:
            # separate instance per account for isolated sessions/proxy
            blu = nexora()
            await process_account(q, i, f"Account-{i+1}", blu, blu.config)

    tasks = [asyncio.create_task(run_one(i, q)) for i, q in enumerate(bot.query_list)]
    await asyncio.gather(*tasks)
    bot.log("🏁 All accounts processed.", Fore.MAGENTA)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n" + Fore.YELLOW + "Interrupted by user. Exiting..." + Fore.RESET)
