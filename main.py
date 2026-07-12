import os
import requests
from time import sleep
import time
from os import system, name
from threading import Thread, active_count
import phonenumbers
from phonenumbers import PhoneNumberFormat
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from bs4 import BeautifulSoup
import random
from emailtools import generate

# Advanced User-Agent Rotation
software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value, SoftwareName.EDGE.value, SoftwareName.OPERA.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value, OperatingSystem.MAC.value]
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=1200)

THREADS = 200
PROXIES_TYPES = ('http', 'socks4', 'socks5')
time_out = 20
success_count = 0
error_count = 0
captcha_count = 0
username = ""

# List of real country codes for more realistic phone numbers
COUNTRY_CODES = [1, 44, 49, 33, 7, 971, 966, 964, 20, 90, 39, 34, 31, 41]

def generate_realistic_phone():
    cc = random.choice(COUNTRY_CODES)
    # Generate a number with 7 to 10 digits
    num = "".join([str(random.randint(0, 9)) for _ in range(random.randint(7, 10))])
    phone_str = f"+{cc}{num}"
    try:
        parsed = phonenumbers.parse(phone_str)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except:
        pass
    return phone_str

def get_random_line(filename, username):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = [l.strip() for l in file.readlines() if l.strip()]
            if not lines:
                return f"Reporting {username} for illegal activities."
            line = random.choice(lines)
            return line.replace('{username}', username)
    except:
        return f"Reporting {username} for illegal activities."

def control(proxy, proxy_type, target_username):
    global success_count, error_count, captcha_count
    
    ua = user_agent_rotator.get_random_user_agent()
    url = 'https://telegram.org/support'
    
    proxies = {
        'http': f'{proxy_type}://{proxy}',
        'https': f'{proxy_type}://{proxy}'
    }
    
    try:
        session = requests.Session()
        session.proxies = proxies
        session.headers.update({
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Step 1: Dynamic Token Extraction
        # We must visit the page first to get CSRF tokens and session cookies
        response = session.get(url, timeout=time_out)
        if response.status_code != 200:
            error_count += 1
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for Captcha immediately
        if "cf-turnstile" in response.text or "g-recaptcha" in response.text:
            captcha_count += 1
            return # Skip this proxy/session as it's flagged

        # Step 2: Prepare Form Data
        message = get_random_line('message.txt', target_username)
        email = generate('gmail')
        phone = generate_realistic_phone()
        
        data = {
            'message': message,
            'legal_name': 'Telegram User',
            'email': email,
            'phone': phone,
            'setln': ''
        }
        
        # Extract ALL hidden inputs (Dynamic Tokens)
        form = soup.find('form', action="/support")
        if not form:
            error_count += 1
            return
            
        for input_tag in form.find_all('input'):
            name_attr = input_tag.get('name')
            if name_attr and name_attr not in data:
                data[name_attr] = input_tag.get('value', '')

        # Human-like delay (0.5 to 2 seconds)
        time.sleep(random.uniform(0.5, 2.0))
        
        # Step 3: Submission with Referer
        session.headers.update({'Referer': url})
        post_response = session.post(url, data=data, timeout=time_out)
        
        if post_response.status_code == 200:
            if "Thank you for your report" in post_response.text or "has been submitted" in post_response.text:
                success_count += 1
            elif "cf-turnstile" in post_response.text:
                captcha_count += 1
            else:
                error_count += 1
        else:
            error_count += 1
            
    except Exception:
        error_count += 1

def worker(proxy_type, proxies_list, target):
    for p in proxies_list:
        control(p.strip(), proxy_type, target)

def start_reporting():
    while True:
        threads = []
        for p_type in PROXIES_TYPES:
            fname = f"{p_type}_proxies.txt"
            if not os.path.exists(fname): continue
            
            with open(fname, 'r') as f:
                proxies = [l for l in f.readlines() if l.strip()]
            
            if not proxies: continue
            
            # Shuffle proxies to avoid pattern detection
            random.shuffle(proxies)
            
            # Split into chunks for threads
            n = max(1, len(proxies) // THREADS)
            chunks = [proxies[i:i + n] for i in range(0, len(proxies), n)]
            
            for chunk in chunks[:THREADS]:
                t = Thread(target=worker, args=(p_type, chunk, username))
                threads.append(t)
                t.start()
        
        for t in threads:
            t.join()
        sleep(2)

def monitor():
    G = '\033[1;32m'
    B = '\033[2;36m'
    S = '\033[1;33m'
    E = '\033[1;31m'
    C = '\033[1;35m'
    while True:
        system('cls' if name == 'nt' else 'clear')
        print(f"Telegram Support Reporter - Ultimate Edition")
        print("-" * 50)
        print(f"{G}[ ACTIVE THREADS ]: {B}{active_count()}")
        print(f"{G}[ SUCCESS REPORTS]: {S}{success_count}")
        print(f"{G}[ FAILED REQUESTS]: {E}{error_count}")
        print(f"{G}[ CAPTCHA BLOCKS ]: {C}{captcha_count}")
        print("-" * 50)
        sleep(5)

if __name__ == "__main__":
    username = input("Enter target (username/link): ")
    Thread(target=start_reporting, daemon=True).start()
    monitor()
