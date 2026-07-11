import os
import requests
from time import sleep
from configparser import ConfigParser
from os import system, name
from threading import Thread, active_count
import csv
import phonenumbers
from phonenumbers import PhoneNumber, PhoneNumberFormat
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from bs4 import BeautifulSoup
import random
from emailtools import generate

software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value, SoftwareName.EDGE.value, SoftwareName.OPERA.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value, OperatingSystem.MAC.value]

user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=1200)

THREADS = 200
PROXIES_TYPES = ('http', 'socks4', 'socks5')

errors = open('errors.txt', 'a+')

time_out = 15
success_count = 0
error_count = 0
username = ""

def generate_random_phone_number():
    while True:
        country_code = "+{}".format(random.randint(1, 999))
        national_number = str(random.randint(1000000000, 9999999999))
        phone_number_str = country_code + national_number
        try:
            phone_number = phonenumbers.parse(phone_number_str)
            if phonenumbers.is_valid_number(phone_number):
                return phonenumbers.format_number(phone_number, PhoneNumberFormat.E164)
        except phonenumbers.phonenumberutil.NumberParseException:
            continue

def get_random_line(filename, username):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            if not lines:
                return f"Reporting {username} for illegal activities."
            line = random.choice(lines).strip()
            return line.replace('{username}', username)
    except FileNotFoundError:
        return f"Reporting {username} for illegal activities."

def control(proxy, proxy_type, username):
    global success_count
    global error_count
    
    USER_AGENT = user_agent_rotator.get_random_user_agent()
    url = 'https://telegram.org/support'
    
    proxy_dict = {
        'http': f'{proxy_type}://{proxy}',
        'https': f'{proxy_type}://{proxy}'
    }
    
    try:
        session = requests.Session()
        session.proxies = proxy_dict
        session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Origin': 'https://telegram.org',
            'Referer': 'https://telegram.org/support'
        })
        
        # Step 1: Get the form and cookies
        response = session.get(url, timeout=time_out)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Step 2: Prepare data with CORRECT field names from HTML analysis
        message = get_random_line('message.txt', username)
        email = generate('gmail')
        phone = generate_random_phone_number()
        
        data = {
            'message': message,      # Correct name for textarea
            'legal_name': 'Telegram User', # Correct name for legal name input
            'email': email,          # Correct name for email input
            'phone': phone,          # Correct name for phone input
            'setln': ''              # Language setting
        }
        
        # Add hidden inputs and other dynamic fields
        form = soup.find('form', action="/support")
        if form:
            for input_tag in form.find_all(['input', 'textarea']):
                name_attr = input_tag.get('name')
                if name_attr and name_attr not in data:
                    data[name_attr] = input_tag.get('value', '')
        
        # Step 3: Post the form
        post_response = session.post(url, data=data, timeout=time_out)
        
        if post_response.status_code == 200:
            # Check for success message in response text
            if "Thank you for your report" in post_response.text or "has been submitted" in post_response.text:
                print(f"Report Successful: {email} | {phone} | Proxy: {proxy}")
                success_count += 1
            else:
                # If 200 but no success message, it might be a captcha wall
                error_count += 1
        else:
            error_count += 1
            
    except Exception as e:
        error_count += 1
        errors.write(f'{proxy} - {e}\n')

def get_views_from_saved_proxies(proxy_type, proxies, username):
    for proxy in proxies:
        control(proxy.strip(), proxy_type, username)

def start_view():
    while True:
        threads = []
        for proxy_type in PROXIES_TYPES:
            filename = f"{proxy_type}_proxies.txt"
            if not os.path.exists(filename):
                continue
            with open(filename, 'r', encoding='utf-8') as file:
                proxies = file.readlines()
            
            if not proxies:
                continue
                
            # Distribute proxies among threads
            chunk_size = max(1, len(proxies) // THREADS)
            chunked_proxies = [proxies[i:i + chunk_size] for i in range(0, len(proxies), chunk_size)]
            
            for chunk in chunked_proxies[:THREADS]:
                thread = Thread(target=get_views_from_saved_proxies, args=(proxy_type, chunk, username))
                threads.append(thread)
                thread.start()
                
        for t in threads:
            t.join()
        sleep(5)

def check_views():
    G = '\033[1;32m'
    B = '\033[2;36m'
    S = '\033[1;33m'
    E = '\033[1;31m'
    while True:
        print(f'{G}[ TOTAL THREADS ]: {B}{active_count()}{G} | [ SUCCESS ]: {S}{success_count}{G} | [ FAILED ]: {E}{error_count}')
        sleep(5)

if __name__ == "__main__":
    print("Telegram Support Reporter - Pro Edition")
    target = input("Enter target (username/link): ")
    username = target
    
    # Start reporting thread
    Thread(target=start_view, daemon=True).start()
    # Start monitoring thread
    check_views()
