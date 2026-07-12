import os
import time
from time import sleep
from os import system, name
from threading import Thread, active_count, Lock
import phonenumbers
from phonenumbers import PhoneNumberFormat
from bs4 import BeautifulSoup
import random
from emailtools import generate
from collections import OrderedDict
from curl_cffi import requests

# --- Advanced Configuration ---
THREADS = 200
PROXIES_TYPES = ('http', 'socks4', 'socks5')
time_out = 35
success_count = 0
error_count = 0
captcha_count = 0
username = ""
counter_lock = Lock()

# Strict Browser Profiles for TLS & Header Consistency (JA3 Support)
BROWSER_PROFILES = [
    {
        "impersonate": "chrome120", # Matches JA3 fingerprint for Chrome
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec_ch_ua_platform": '"Windows"',
        "headers": ["Host", "Connection", "Sec-Ch-Ua", "Sec-Ch-Ua-Mobile", "User-Agent", "Sec-Ch-Ua-Platform", "Accept", "Sec-Fetch-Site", "Sec-Fetch-Mode", "Sec-Fetch-Dest", "Referer", "Accept-Encoding", "Accept-Language"]
    },
    {
        "impersonate": "firefox120", # Matches JA3 fingerprint for Firefox
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "headers": ["Host", "User-Agent", "Accept", "Accept-Language", "Accept-Encoding", "Connection", "Referer", "Upgrade-Insecure-Requests", "Sec-Fetch-Dest", "Sec-Fetch-Mode", "Sec-Fetch-Site"]
    }
]

LANGUAGES = ['en-US,en;q=0.9', 'en-GB,en;q=0.8', 'ar-SA,ar;q=0.9,en;q=0.8']

def update_counter(type):
    global success_count, error_count, captcha_count
    with counter_lock:
        if type == 'success': success_count += 1
        elif type == 'error': error_count += 1
        elif type == 'captcha': captcha_count += 1

def generate_realistic_phone():
    cc = random.choice([1, 44, 49, 33, 7, 971, 966, 964, 20, 90])
    num = "".join([str(random.randint(0, 9)) for _ in range(random.randint(7, 10))])
    phone_str = f"+{cc}{num}"
    try:
        parsed = phonenumbers.parse(phone_str)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except: pass
    return phone_str

def get_random_line(filename, target):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = [l.strip() for l in file.readlines() if l.strip()]
            return random.choice(lines).replace('{username}', target) if lines else f"Reporting {target}"
    except: return f"Reporting {target}"

def control(proxy, proxy_type, target_username):
    url = 'https://telegram.org/support'
    profile = random.choice(BROWSER_PROFILES)
    
    proxies = {
        'http': f'{proxy_type}://{proxy}',
        'https': f'{proxy_type}://{proxy}'
    }
    
    try:
        # Using curl_cffi Session for TLS Impersonation (JA3)
        session = requests.Session(impersonate=profile["impersonate"])
        session.proxies = proxies
        
        # Human Behavior: Pre-load assets simulation
        if random.random() > 0.5:
            home = session.get('https://telegram.org/', timeout=time_out)
            # Simulate loading a few static assets (CSS/JS)
            if home.status_code == 200:
                h_soup = BeautifulSoup(home.text, 'html.parser')
                assets = [a.get('src') or a.get('href') for a in h_soup.find_all(['script', 'link'])[:3]]
                for asset in assets:
                    if asset and asset.startswith('/'):
                        session.get(f'https://telegram.org{asset}', timeout=time_out)
            time.sleep(random.uniform(2, 5))

        # Step 1: Fetch Support Page & Dynamic Tokens
        session.headers.update({
            "User-Agent": profile["ua"],
            "Accept-Language": random.choice(LANGUAGES),
            "Sec-Ch-Ua": profile.get("sec_ch_ua", ""),
            "Sec-Ch-Ua-Platform": profile.get("sec_ch_ua_platform", "")
        })
        
        response = session.get(url, timeout=time_out)
        if response.status_code != 200:
            update_counter('error')
            return

        if "cf-turnstile" in response.text or "g-recaptcha" in response.text:
            update_counter('captcha')
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', action="/support")
        if not form:
            update_counter('error')
            return

        # Step 2: Prepare Data & Human Delay
        data = {
            'message': get_random_line('message.txt', target_username),
            'legal_name': 'Telegram User',
            'email': generate('gmail'),
            'phone': generate_realistic_phone(),
            'setln': ''
        }
        
        for input_tag in form.find_all('input'):
            name_attr = input_tag.get('name')
            if name_attr and name_attr not in data:
                data[name_attr] = input_tag.get('value', '')

        time.sleep(random.uniform(3, 7)) # Simulate thinking/typing
        
        # Step 3: Final Submission
        session.headers.update({
            'Referer': url,
            'Origin': 'https://telegram.org',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        post_response = session.post(url, data=data, timeout=time_out)
        
        if post_response.status_code == 200:
            if "Thank you for your report" in post_response.text or "has been submitted" in post_response.text:
                update_counter('success')
            else:
                update_counter('error')
        else:
            update_counter('error')
            
    except Exception:
        update_counter('error')

def worker(proxy_type, proxies_list, target):
    for p in proxies_list:
        control(p.strip(), proxy_type, target)
        time.sleep(random.uniform(2, 6))

def start_reporting():
    while True:
        threads = []
        for p_type in PROXIES_TYPES:
            fname = f"{p_type}_proxies.txt"
            if not os.path.exists(fname): continue
            with open(fname, 'r') as f:
                proxies = [l for l in f.readlines() if l.strip()]
            if not proxies: continue
            random.shuffle(proxies)
            n = max(1, len(proxies) // THREADS)
            chunks = [proxies[i:i + n] for i in range(0, len(proxies), n)]
            for chunk in chunks[:THREADS]:
                t = Thread(target=worker, args=(p_type, chunk, username))
                threads.append(t)
                t.start()
        for t in threads: t.join()
        sleep(3)

def monitor():
    while True:
        system('cls' if name == 'nt' else 'clear')
        print(f"Telegram Support Reporter - Ghost Edition (TLS JA3)")
        print("-" * 50)
        print(f"[ ACTIVE THREADS ]: {active_count()}")
        print(f"[ SUCCESS REPORTS]: {success_count}")
        print(f"[ FAILED REQUESTS]: {error_count}")
        print(f"[ CAPTCHA BLOCKS ]: {captcha_count}")
        print("-" * 50)
        sleep(5)

if __name__ == "__main__":
    username = input("Enter target (username/link): ")
    Thread(target=start_reporting, daemon=True).start()
    monitor()
