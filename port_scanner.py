"""
NetScanner v2 — اسکنر پورت موازی برای سیستم شخصی/آزمایشگاه
امکانات: اسکن همزمان، بازه دلخواه، پورت‌های رایج، تشخیص سرویس، خروجی JSON

⚠️ فقط برای سیستم خودتان یا آزمایشگاه شخصی با مجوز. اسکن دیگران بدون
مجوز کتبی جرم است.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import List, Optional

COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
    993, 995, 1723, 3306, 3389, 5432, 5900, 6379, 8000, 8080,
    8443, 8888, 9090, 27017,
]


@dataclass
class ScanResult:
    """نتیجه اسکن یک پورت"""
    port: int
    state: str          # "open" یا "closed"
    service: Optional[str] = None
    banner: Optional[str] = None


def get_service_name(port: int) -> Optional[str]:
    """نام استاندارد سرویس را برمی‌گرداند (مثل http برای ۸۰)"""
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return None


def grab_banner(host: str, port: int, timeout: float = 1.0) -> Optional[str]:
    """اتصال کوتاه باز می‌کند و متنی که سرویس می‌فرستد را می‌خواند"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            s.sendall(b"\r\n")
            data = s.recv(100)
        text = data.decode("utf-8", errors="replace").strip()
        return text if text else None
    except (socket.error, OSError):
        return None


def scan_one(host: str, port: int, timeout: float, grab: bool) -> ScanResult:
    """اسکن یک پورت: باز/بسته + سرویس + بنر (اختیاری)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            is_open = s.connect_ex((host, port)) == 0
    except (socket.error, OverflowError):
        is_open = False

    if not is_open:
        return ScanResult(port=port, state="closed")

    result = ScanResult(port=port, state="open", service=get_service_name(port))
    if grab:
        result.banner = grab_banner(host, port)
    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="اسکنر پورت موازی — فقط برای سیستم خودتان یا آزمایشگاه مجاز",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--host", default="127.0.0.1", help="آدرس IP یا نام دامنه")
    p.add_argument("--start", type=int, default=1, help="پورت شروع")
    p.add_argument("--end", type=int, default=1024, help="پورت پایان")
    p.add_argument("--timeout", type=float, default=0.3, help="مهلت اتصال هر پورت (ثانیه)")
    p.add_argument("--threads", type=int, default=50, help="تعداد نخ‌های همزمان")
    p.add_argument("--common", action="store_true", help="فقط پورت‌های رایج را اسکن کن")
    p.add_argument("--banner", action="store_true", help="خواندن بنر سرویس (فقط آزمایشگاه)")
    p.add_argument("--json", dest="json_out", metavar="FILE", help="ذخیره خروجی در فایل JSON")
    return p.parse_args()


def resolve_host(host: str) -> str:
    """اگر نام دامنه بود، به IP تبدیل می‌کند"""
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        return socket.gethostbyname(host)


def confirm_if_remote(host: str) -> None:
    """اگر هاست غیرمحلی است، تأیید آگاهانه بگیر"""
    if host in {"127.0.0.1", "::1", "localhost"}:
        return
    print("⚠️  هاست غیرمحلی انتخاب شده است.")
    answer = input("این سیستم متعلق به خودت است یا مجوز کتبی داری؟ (yes/no): ").strip().lower()
    if answer != "yes":
        print("خروج...")
        sys.exit(1)


def build_port_list(args: argparse.Namespace) -> List[int]:
    if args.common:
        return COMMON_PORTS
    if not (1 <= args.start <= args.end <= 65535):
        raise ValueError("بازه پورت باید بین ۱ تا ۶۵۵۳۵ باشد")
    return list(range(args.start, args.end + 1))


def main() -> None:
    args = parse_args()
    try:
        host = resolve_host(args.host)
        ports = build_port_list(args)
    except (ValueError, socket.gaierror) as e:
        print(f"❌ خطا در ورودی: {e}")
        sys.exit(2)

    confirm_if_remote(host)

    print(f"[*] اسکن {host} — {len(ports)} پورت با {args.threads} نخ ...")
    start_time = time.perf_counter()
    open_results: List[ScanResult] = []

    try:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = {
                executor.submit(scan_one, host, port, args.timeout, args.banner): port
                for port in ports
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                except Exception:
                    continue  # خطای یک پورت نباید کل اسکن را متوقف کند

                if result.state == "open":
                    open_results.append(result)
                    line = f"[+] پورت {result.port} باز است"
                    if result.service:
                        line += f"  ({result.service})"
                    if result.banner:
                        line += f"  → {result.banner[:60]}"
                    print(line)
    except KeyboardInterrupt:
        print("\n[!] متوقف شد (Ctrl+C)")

    elapsed = time.perf_counter() - start_time
    print("-" * 50)
    print(f"[✓] پایان اسکن: {len(open_results)} پورت باز در {elapsed:.2f} ثانیه")

    if args.json_out:
        payload = {
            "host": host,
            "duration_seconds": round(elapsed, 2),
            "open_ports": [asdict(r) for r in open_results],
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[*] خروجی در {args.json_out} ذخیره شد")


if __name__ == "__main__":
    main()
