#!/usr/bin/env python3
import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

class AdminPanelFinder:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Linux; Android 10; SM-A505FN)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        ]
        self.timeout = 10
        self.delay = 0.5
        self.max_threads = 15
        self.found_panels = []
        
    def load_wordlist(self, wordlist_path="admin_wordlist.txt"):
        try:
            with open(wordlist_path, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"[!] Wordlist bulunamadı: {wordlist_path}")
            return self.default_paths()
    
    def default_paths(self):
        return [
            "/admin", "/wp-admin", "/administrator", "/panel", 
            "/login", "/admin.php", "/admin/login", "/adminpanel",
            "/user/login", "/backend", "/cms", "/manager",
            "/admin_area", "/controlpanel", "/admincp", "/admincenter",
            "/secret-admin", "/myadmin", "/system", "/console"
        ]
    
    def get_random_agent(self):
        return random.choice(self.user_agents)
    
    def check_url(self, base_url, path, proxies=None):
        url = urljoin(base_url, path)
        headers = {"User-Agent": self.get_random_agent()}
        
        try:
            time.sleep(self.delay)  # Rate limiting
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                proxies=proxies,
                allow_redirects=False
            )
            
            if response.status_code == 200:
                content_length = len(response.content)
                title = self.extract_title(response.text)
                self.found_panels.append((url, response.status_code, content_length, title))
                return True
                
        except Exception as e:
            pass
        return False
    
    def extract_title(self, html):
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            return soup.title.string if soup.title else "No Title"
        except:
            return "No Title"
    
    def analyze_robots(self, base_url, proxies=None):
        robots_url = urljoin(base_url, "/robots.txt")
        try:
            response = requests.get(robots_url, timeout=self.timeout, proxies=proxies)
            if response.status_code == 200:
                disallowed_paths = [
                    line.split(": ")[1].strip() 
                    for line in response.text.splitlines() 
                    if line.startswith("Disallow:")
                ]
                return disallowed_paths
        except:
            pass
        return []
    
    def analyze_sitemap(self, base_url, proxies=None):
        sitemap_urls = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap.php"
        ]
        for path in sitemap_urls:
            url = urljoin(base_url, path)
            try:
                response = requests.get(url, timeout=self.timeout, proxies=proxies)
                if response.status_code == 200:
                    # Basit sitemap analizi
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'xml')
                    urls = [loc.text for loc in soup.find_all('loc')]
                    admin_urls = [u for u in urls if any(p in u.lower() for p in ["admin", "login", "panel"])]
                    return admin_urls
            except:
                continue
        return []
    
    def scan(self, target, wordlist_path=None, proxies=None):
        if not target.startswith(("http://", "https://")):
            target = "http://" + target
        
        print(f"\n[+] Target: {target}")
        print("[+] Scanning started...\n")
        
        # Wordlist yükle
        paths = self.load_wordlist(wordlist_path) if wordlist_path else self.default_paths()
        
        # Robots.txt ve sitemap analizi
        print("[*] Analyzing robots.txt and sitemap...")
        extra_paths = self.analyze_robots(target, proxies)
        extra_paths.extend(self.analyze_sitemap(target, proxies))
        paths.extend(extra_paths)
        paths = list(set(paths))  # Tekrar edenleri kaldır
        
        print(f"[*] Testing {len(paths)} paths with {self.max_threads} threads...")
        
        # Çoklu thread ile tarama
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [
                executor.submit(self.check_url, target, path, proxies) 
                for path in paths
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    pass
        
        # Sonuçları göster
        self.show_results()
    
    def show_results(self):
        if not self.found_panels:
            print("\n[-] No admin panels found!")
            return
            
        print("\n[+] Found admin panels:")
        print("{:<60} {:<10} {:<10} {:<30}".format("URL", "Status", "Size", "Title"))
        print("-" * 110)
        for url, status, size, title in self.found_panels:
            print("{:<60} {:<10} {:<10} {:<30}".format(url, status, size, title))

def main():
    banner = """
    █████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗    ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
   ██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║    ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
   ███████║██║  ██║██╔████╔██║██║██╔██╗ ██║    █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
   ██╔══██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║    ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
   ██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║    ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
   ╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
   Advanced Admin Panel Finder v2.0 By Quantumpeak
   """
    print(banner)
    
    finder = AdminPanelFinder()
    
    target = input("[?] Target URL (example.com or http://example.com): ").strip()
    wordlist = input("[?] Custom wordlist path (leave blank for default): ").strip() or None
    
    # Proxy ayarları (isteğe bağlı)
    use_proxy = input("[?] Use proxy? (y/n): ").lower() == 'y'
    proxies = None
    if use_proxy:
        proxy_url = input("[?] Enter proxy (http://ip:port): ").strip()
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
    
    finder.scan(target, wordlist_path=wordlist, proxies=proxies)

if __name__ == "__main__":
    main()
