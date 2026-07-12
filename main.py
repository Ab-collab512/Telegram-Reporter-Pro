import os
import requests
from time import sleep
import time
from os import system, name
from threading import Thread, active_count, Lock
import phonenumbers
from phonenumbers import PhoneNumberFormat
from bs4 import BeautifulSoup
import random
from emailtools import generate
from collections import OrderedDict

# --- Configuration & Global Variables ---
THREADS = 200
PROXIES_TYPES = ('http', 'socks4', 'socks5')
time_out = 30
success_count = 0
error_count = 0
captcha_count = 0
username = ""

# Thread Lock for Safe Counter Updates (Prevents Race Conditions)
counter_lock = Lock()

# Advanced Browser Profiles for Full Fingerprinting
LANGUAGES = ['en-US,en;q=0.9', 'en-GB,en;q=0.8', 'ar-SA,ar;q=0.9,en;q=0.8', 'fr-FR,fr;q=0.9,en;q=0.8', 'de-DE,de;q=0.9,en;q=0.8']

BROWSER_PROFILES = [
    {
        "browser": "Chrome",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "sec_ch_ua": '"Not A(Bit:Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "sec_ch_ua_platform": '"Windows"',
        "headers_order": ["Host", "Connection", "Sec-Ch-Ua", "Sec-Ch-Ua-Mobile", "User-Agent", "Sec-Ch-Ua-Platform", "Accept", "Sec-Fetch-Site", "Sec-Fetch-Mode", "Sec-Fetch-Dest", "Referer", "Accept-Encoding", "Accept-Language"]
    },
    {
        "browser": "Firefox",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "headers_order": ["Host", "User-Agent", "Accept", "Accept-Language", "Accept-Encoding", "Connection", "Referer", "Upgrade-Insecure-Requests", "Sec-Fetch-Dest", "Sec-Fetch-Mode", "Sec-Fetch-Site"]
    }
]

def update_success():
    global success_count
    with counter_lock:
        success_count += 1

def update_error():
    global error_count
    with counter_lock:
        error_count += 1

def update_captcha():
    global captcha_count
    with counter_lock:
        captcha_count += 1

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

def get_session_with_fingerprint(proxy, proxy_type):
    profile = random.choice(BROWSER_PROFILES)
    session = requests.Session()
    session.proxies = {'http': f'{proxy_type}://{proxy}', 'https': f'{proxy_type}://{proxy}'}
    
    headers = OrderedDict()
    for h in profile["headers_order"]:
        if h == "Host": headers[h] = "telegram.org"
        elif h == "Connection": headers[h] = "keep-alive"
        elif h == "User-Agent": headers[h] = profile["ua"]
        elif h == "Sec-Ch-Ua": headers[h] = profile.get("sec_ch_ua", "")
        elif h == "Sec-Ch-Ua-Mobile": headers[h] = "?0"
        elif h == "Sec-Ch-Ua-Platform": headers[h] = profile.get("sec_ch_ua_platform", "")
        elif h == "Accept": headers[h] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        elif h == "Sec-Fetch-Site": headers[h] = "same-origin"
        elif h == "Sec-Fetch-Mode": headers[h] = "navigate"
        elif h == "Sec-Fetch-Dest": headers[h] = "document"
        elif h == "Accept-Encoding": headers[h] = "gzip, deflate, br"
        elif h == "Accept-Language": headers[h] = random.choice(LANGUAGES)
        elif h == "Upgrade-Insecure-Requests": headers[h] = "1"
    
    session.headers = headers
    return session

def control(proxy, proxy_type, target_username):
    url = 'https://telegram.org/support'
    try:
        session = get_session_with_fingerprint(proxy, proxy_type)
        
        # Step 1: Pre-interaction (Human-like)
        if random.random() > 0.6:
            session.get('https://telegram.org/', timeout=time_out)
            time.sleep(random.uniform(1, 4))

        # Step 2: Fetch Form & Dynamic Tokens
        response = session.get(url, timeout=time_out)
        if response.status_code != 200:
            update_error()
            return

        if "cf-turnstile" in response.text or "g-recaptcha" in response.text:
            update_captcha()
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', action="/support")
        if not form:
            update_error()
            return

        # Step 3: Fill Data & Simulate Typing Time
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

        # Human typing simulation (2-6 seconds)
        time.sleep(random.uniform(2, 6))
        
        # Step 4: Secure Submission
        session.headers['Referer'] = url
        session.headers['Origin'] = 'https://telegram.org'
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        post_response = session.post(url, data=data, timeout=time_out)
        
        if post_response.status_code == 200:
            if "Thank you for your report" in post_response.text or "has been submitted" in post_response.text:
                update_success()
            else:
                update_error()
        else:
            update_error()
            
    except Exception:
        update_error()

def worker(proxy_type, proxies_list, target):
    for p in proxies_list:
        control(p.strip(), proxy_type, target)
        # Random rest between requests from the same thread
        time.sleep(random.uniform(1, 5))

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
        sleep(2)

def monitor():
    while True:
        system('cls' if name == 'nt' else 'clear')
        print(f"Telegram Support Reporter - Pro Anti-Detection")
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
