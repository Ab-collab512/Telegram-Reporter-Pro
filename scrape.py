import os
import requests
from time import sleep
from configparser import ConfigParser
from threading import Thread
from re import compile

THREADS = 200
PROXIES_TYPES = ('http', 'socks4', 'socks5')
REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

def save_proxies(proxies, proxy_type):
    with open(f"{proxy_type}_proxies.txt", 'w') as file:
        for proxy in proxies:
            file.write(proxy + '\n')
    print(f"[ SCRAPER ] Saved {len(proxies)} {proxy_type} proxies.")

def scrap(sources, _proxy_type):
    proxies = []
    for source in sources:
        source = source.strip()
        if source:
            try:
                response = requests.get(source, timeout=15)
                matches = REGEX.findall(response.text)
                for match in matches:
                    proxies.append(match[0])
            except:
                pass
    save_proxies(list(set(proxies)), _proxy_type)

def start_scrap():
    cfg = ConfigParser(interpolation=None)
    if not os.path.exists("config.ini"):
        print("[ ERROR ] config.ini not found!")
        return

    cfg.read("config.ini", encoding="utf-8")
    threads = []
    
    for p_type in PROXIES_TYPES:
        if p_type.upper() in cfg:
            sources = cfg[p_type.upper()].get("Sources", "").splitlines()
            thread = Thread(target=scrap, args=(sources, p_type))
            threads.append(thread)
            thread.start()
            
    for t in threads:
        t.join()

if __name__ == "__main__":
    while True:
        print("[ SCRAPER ] Starting proxy collection...")
        start_scrap()
        print("[ SCRAPER ] Collection finished. Waiting 10 minutes for next update.")
        sleep(600)
