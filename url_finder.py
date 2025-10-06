#!/usr/bin/env python3

import requests
import argparse
import sys
import re
import time
import threading
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

init(autoreset=True)

ASCII_ART = f"""{Fore.CYAN}
██╗   ██╗██████╗ ██╗         ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
██║   ██║██╔══██╗██║         ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
██║   ██║██████╔╝██║         █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
██║   ██║██╔══██╗██║         ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║███████╗    ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
{Style.RESET_ALL}
{Fore.YELLOW}     Advanced URL Discovery Tool - Extract All URLs from Websites{Style.RESET_ALL}
{Fore.GREEN}        Developed by: S.Tamilselvan{Style.RESET_ALL}
{Fore.MAGENTA}        GitHub: https://github.com/Tamilselvan-S-Cyber-Security{Style.RESET_ALL}
{Fore.CYAN}        Official Site: https://tamilselvan-official.web.app/{Style.RESET_ALL}
{Fore.WHITE}        ════════════════════════════════════════════════════════════{Style.RESET_ALL}
"""

class URLFinder:
    def __init__(self, target_url, output_file):
        self.target_url = target_url
        self.output_file = output_file
        self.found_urls = set()
        self.internal_urls = set()
        self.external_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.spinner_active = False
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.base_domain = urlparse(target_url).netloc
        
    def spinner_animation(self, message):
        idx = 0
        while self.spinner_active:
            sys.stdout.write(f'\r{Fore.CYAN}{self.spinner_chars[idx]} {message}{Style.RESET_ALL}')
            sys.stdout.flush()
            idx = (idx + 1) % len(self.spinner_chars)
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()
    
    def progress_bar(self, current, total, message=""):
        bar_length = 40
        progress = float(current) / float(total) if total > 0 else 0
        block = int(bar_length * progress)
        bar = '█' * block + '░' * (bar_length - block)
        percentage = progress * 100
        sys.stdout.write(f'\r{Fore.CYAN}[{bar}] {percentage:.1f}% {message}{Style.RESET_ALL}')
        sys.stdout.flush()
        if current >= total:
            print()
    
    def fetch_page(self, url):
        try:
            self.spinner_active = True
            spinner_thread = threading.Thread(target=self.spinner_animation, args=(f"Fetching {url[:50]}...",))
            spinner_thread.start()
            
            response = self.session.get(url, timeout=15, allow_redirects=True)
            
            self.spinner_active = False
            spinner_thread.join()
            
            if response.status_code == 200:
                print(f"{Fore.GREEN}[+] Successfully fetched URL (Status: {response.status_code}){Style.RESET_ALL}")
                return response
            else:
                print(f"{Fore.YELLOW}[!] Fetched with status code: {response.status_code}{Style.RESET_ALL}")
                return response
        except requests.exceptions.RequestException as e:
            self.spinner_active = False
            print(f"{Fore.RED}[-] Error fetching URL: {str(e)[:60]}{Style.RESET_ALL}")
            return None
    
    def extract_urls_from_html(self, soup, base_url):
        urls = set()
        
        for tag in soup.find_all(['a', 'link']):
            href = tag.get('href')
            if href:
                full_url = urljoin(base_url, href)
                urls.add(full_url)
        
        for tag in soup.find_all(['img', 'script', 'iframe', 'embed', 'source']):
            src = tag.get('src')
            if src:
                full_url = urljoin(base_url, src)
                urls.add(full_url)
        
        for tag in soup.find_all(['form']):
            action = tag.get('action')
            if action:
                full_url = urljoin(base_url, action)
                urls.add(full_url)
        
        return urls
    
    def extract_urls_from_text(self, text, base_url):
        urls = set()
        
        url_pattern = r'https?://[^\s\'"<>)}\]]+|www\.[^\s\'"<>)}\]]+'
        matches = re.findall(url_pattern, text)
        
        for match in matches:
            if match.startswith('www.'):
                match = 'http://' + match
            full_url = urljoin(base_url, match)
            urls.add(full_url)
        
        relative_pattern = r'["\']([/][^"\'\s]+)["\']'
        relative_matches = re.findall(relative_pattern, text)
        
        for match in relative_matches:
            full_url = urljoin(base_url, match)
            urls.add(full_url)
        
        return urls
    
    def extract_urls_from_javascript(self, soup, base_url):
        urls = set()
        
        for script in soup.find_all('script'):
            if script.string:
                js_urls = self.extract_urls_from_text(script.string, base_url)
                urls.update(js_urls)
        
        return urls
    
    def categorize_urls(self):
        for url in self.found_urls:
            parsed = urlparse(url)
            if parsed.netloc == self.base_domain or parsed.netloc == '':
                self.internal_urls.add(url)
            else:
                self.external_urls.add(url)
    
    def clean_url(self, url):
        parsed = urlparse(url)
        if parsed.fragment:
            url = url.split('#')[0]
        return url
    
    def discover_urls(self):
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Starting URL Discovery...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.MAGENTA}[>] Target: {self.target_url}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}[>] Domain: {self.base_domain}{Style.RESET_ALL}\n")
        
        response = self.fetch_page(self.target_url)
        
        if not response:
            print(f"{Fore.RED}[-] Failed to fetch target URL{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}[*] Extracting URLs from different sources...{Style.RESET_ALL}\n")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tasks = [
            ("HTML elements", self.extract_urls_from_html, soup, self.target_url),
            ("JavaScript code", self.extract_urls_from_javascript, soup, self.target_url),
            ("Raw text content", self.extract_urls_from_text, response.text, self.target_url)
        ]
        
        total_tasks = len(tasks)
        for idx, (name, func, *args) in enumerate(tasks, 1):
            self.spinner_active = True
            spinner_thread = threading.Thread(target=self.spinner_animation, args=(f"Scanning {name}...",))
            spinner_thread.start()
            
            time.sleep(0.3)
            urls = func(*args)
            
            self.spinner_active = False
            spinner_thread.join()
            
            self.found_urls.update(urls)
            print(f"{Fore.GREEN}[+] Extracted from {name}: {len(urls)} URLs{Style.RESET_ALL}")
            self.progress_bar(idx, total_tasks, f"Progress {idx}/{total_tasks}")
        
        self.found_urls = {self.clean_url(url) for url in self.found_urls}
        
        print(f"\n{Fore.CYAN}[*] Categorizing URLs...{Style.RESET_ALL}")
        self.categorize_urls()
        
        self.generate_report()
    
    def generate_report(self):
        self.spinner_active = True
        spinner_thread = threading.Thread(target=self.spinner_animation, args=("Generating report...",))
        spinner_thread.start()
        time.sleep(1)
        self.spinner_active = False
        spinner_thread.join()
        
        print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] URL Discovery Complete!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
        
        total_urls = len(self.found_urls)
        internal_count = len(self.internal_urls)
        external_count = len(self.external_urls)
        
        print(f"{Fore.CYAN}[*] Statistics:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ├─ Total URLs Found: {Fore.YELLOW}{total_urls}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ├─ Internal URLs: {Fore.GREEN}{internal_count}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  └─ External URLs: {Fore.MAGENTA}{external_count}{Style.RESET_ALL}\n")
        
        with open(self.output_file, 'w') as f:
            f.write("URL Finder - URL Discovery Report\n")
            f.write("="*70 + "\n")
            f.write(f"Developed by: S.Tamilselvan\n")
            f.write(f"GitHub: https://github.com/Tamilselvan-S-Cyber-Security\n")
            f.write(f"Official Site: https://tamilselvan-official.web.app/\n")
            f.write("="*70 + "\n\n")
            f.write(f"Target URL: {self.target_url}\n")
            f.write(f"Base Domain: {self.base_domain}\n\n")
            f.write(f"Statistics:\n")
            f.write(f"  - Total URLs: {total_urls}\n")
            f.write(f"  - Internal URLs: {internal_count}\n")
            f.write(f"  - External URLs: {external_count}\n\n")
            f.write("-"*70 + "\n")
            
            if self.internal_urls:
                f.write(f"\nInternal URLs ({internal_count}):\n")
                f.write("-"*70 + "\n")
                for url in sorted(self.internal_urls):
                    f.write(f"{url}\n")
            
            if self.external_urls:
                f.write(f"\nExternal URLs ({external_count}):\n")
                f.write("-"*70 + "\n")
                for url in sorted(self.external_urls):
                    f.write(f"{url}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("All URLs (Combined):\n")
            f.write("="*70 + "\n")
            for url in sorted(self.found_urls):
                f.write(f"{url}\n")
        
        print(f"{Fore.GREEN}[+] Report saved to: {Fore.YELLOW}{self.output_file}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[i] You can now use these URLs for testing with Devil_Xss scanner!{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}[*] Tip: Use this command to test the URLs:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}     python devil_xss.py -f {self.output_file} -p payloads.txt -o results.txt{Style.RESET_ALL}\n")

def main():
    print(ASCII_ART)
    
    parser = argparse.ArgumentParser(
        description='URL Finder - Advanced URL Discovery Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-u', '--url', required=True, help='Target URL to scan for URLs')
    parser.add_argument('-o', '--output', required=True, help='Output file to store discovered URLs')
    
    args = parser.parse_args()
    
    if not args.url.startswith(('http://', 'https://')):
        print(f"{Fore.RED}[-] Error: URL must start with http:// or https://{Style.RESET_ALL}")
        sys.exit(1)
    
    finder = URLFinder(args.url, args.output)
    finder.discover_urls()

if __name__ == '__main__':
    main()
