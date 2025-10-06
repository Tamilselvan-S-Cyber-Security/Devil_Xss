#!/usr/bin/env python3

import requests
import argparse
import sys
import re
import time
import threading
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

init(autoreset=True)

ASCII_ART = f"""{Fore.RED}
██████╗ ███████╗██╗   ██╗██╗██╗         ██╗  ██╗███████╗███████╗
██╔══██╗██╔════╝██║   ██║██║██║         ╚██╗██╔╝██╔════╝██╔════╝
██║  ██║█████╗  ██║   ██║██║██║          ╚███╔╝ ███████╗███████╗
██║  ██║██╔══╝  ╚██╗ ██╔╝██║██║          ██╔██╗ ╚════██║╚════██║
██████╔╝███████╗ ╚████╔╝ ██║███████╗    ██╔╝ ██╗███████║███████║
╚═════╝ ╚══════╝  ╚═══╝  ╚═╝╚══════╝    ╚═╝  ╚═╝╚══════╝╚══════╝
{Style.RESET_ALL}
{Fore.CYAN}        XSS Vulnerability Scanner - Find All XSS Vulnerabilities{Style.RESET_ALL}
{Fore.YELLOW}        Developed by: S.Tamilselvan{Style.RESET_ALL}
{Fore.GREEN}        GitHub: https://github.com/Tamilselvan-S-Cyber-Security{Style.RESET_ALL}
{Fore.MAGENTA}        Official Site: https://tamilselvan-official.web.app/{Style.RESET_ALL}
{Fore.WHITE}        ═══════════════════════════════════════════════════════════{Style.RESET_ALL}
"""

class DevilXSS:
    def __init__(self, urls_file, payloads_file, output_file):
        self.urls_file = urls_file
        self.payloads_file = payloads_file
        self.output_file = output_file
        self.urls = []
        self.payloads = []
        self.vulnerabilities = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.spinner_active = False
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        
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
        progress = float(current) / float(total)
        block = int(bar_length * progress)
        bar = '█' * block + '░' * (bar_length - block)
        percentage = progress * 100
        sys.stdout.write(f'\r{Fore.CYAN}[{bar}] {percentage:.1f}% {message}{Style.RESET_ALL}')
        sys.stdout.flush()
        if current == total:
            print()
        
    def load_urls(self):
        try:
            self.spinner_active = True
            spinner_thread = threading.Thread(target=self.spinner_animation, args=("Loading URLs...",))
            spinner_thread.start()
            
            time.sleep(0.5)
            with open(self.urls_file, 'r') as f:
                self.urls = [line.strip() for line in f if line.strip()]
            
            self.spinner_active = False
            spinner_thread.join()
            print(f"{Fore.GREEN}[+] Loaded {len(self.urls)} URLs successfully{Style.RESET_ALL}")
        except FileNotFoundError:
            self.spinner_active = False
            print(f"{Fore.RED}[!] URLs file not found: {self.urls_file}{Style.RESET_ALL}")
            sys.exit(1)
            
    def load_payloads(self):
        try:
            self.spinner_active = True
            spinner_thread = threading.Thread(target=self.spinner_animation, args=("Loading payloads...",))
            spinner_thread.start()
            
            time.sleep(0.5)
            with open(self.payloads_file, 'r') as f:
                self.payloads = [line.strip() for line in f if line.strip()]
            
            self.spinner_active = False
            spinner_thread.join()
            print(f"{Fore.GREEN}[+] Loaded {len(self.payloads)} XSS payloads successfully{Style.RESET_ALL}")
        except FileNotFoundError:
            self.spinner_active = False
            print(f"{Fore.RED}[!] Payloads file not found: {self.payloads_file}{Style.RESET_ALL}")
            sys.exit(1)
            
    def test_reflected_xss_get(self, url, payload):
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        
        if not params:
            params = {'q': ''}
        
        for param_name in params.keys():
            test_params = params.copy()
            test_params[param_name] = payload
            
            new_query = urlencode(test_params, doseq=True)
            test_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            try:
                response = self.session.get(test_url, timeout=10, allow_redirects=True)
                status_code = response.status_code
                
                if payload in response.text:
                    vuln_info = {
                        'url': test_url,
                        'method': 'GET',
                        'parameter': param_name,
                        'payload': payload,
                        'status_code': status_code
                    }
                    self.vulnerabilities.append(vuln_info)
                    print(f"\n{Fore.RED}[VULNERABLE] {test_url}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}  ├─ Method: GET | Param: {param_name} | Status: {status_code}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}  └─ Payload: {payload[:60]}{'...' if len(payload) > 60 else ''}{Style.RESET_ALL}\n")
                    return True
                    
            except requests.exceptions.RequestException:
                pass
                
        return False
    
    def test_reflected_xss_post(self, url, payload):
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            forms = soup.find_all('form')
            
            for form in forms:
                form_details = self.get_form_details(form)
                
                for input_name in form_details['inputs']:
                    form_data = {}
                    for inp in form_details['inputs']:
                        if inp == input_name:
                            form_data[inp] = payload
                        else:
                            form_data[inp] = 'test'
                    
                    if form_details['action'] == '':
                        form_url = url
                    else:
                        form_url = urljoin(url, form_details['action'])
                    
                    try:
                        if form_details['method'].lower() == 'post':
                            resp = self.session.post(form_url, data=form_data, timeout=10)
                        else:
                            resp = self.session.get(form_url, params=form_data, timeout=10)
                        
                        status_code = resp.status_code
                        
                        if payload in resp.text:
                            vuln_info = {
                                'url': form_url,
                                'method': form_details['method'].upper(),
                                'parameter': input_name,
                                'payload': payload,
                                'status_code': status_code
                            }
                            self.vulnerabilities.append(vuln_info)
                            print(f"\n{Fore.RED}[💀 VULNERABLE] {form_url}{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}  ├─ Method: {form_details['method'].upper()} | Param: {input_name} | Status: {status_code}{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}  └─ Payload: {payload[:60]}{'...' if len(payload) > 60 else ''}{Style.RESET_ALL}\n")
                            return True
                            
                    except requests.exceptions.RequestException:
                        pass
                        
        except Exception:
            pass
            
        return False
    
    def get_form_details(self, form):
        details = {}
        action = form.attrs.get('action', '')
        method = form.attrs.get('method', 'get')
        inputs = []
        
        for input_tag in form.find_all('input'):
            input_name = input_tag.attrs.get('name')
            if input_name:
                inputs.append(input_name)
                
        for textarea in form.find_all('textarea'):
            textarea_name = textarea.attrs.get('name')
            if textarea_name:
                inputs.append(textarea_name)
        
        details['action'] = action
        details['method'] = method
        details['inputs'] = inputs
        
        return details
    
    def test_header_xss(self, url, payload):
        headers_to_test = ['User-Agent', 'Referer', 'X-Forwarded-For']
        
        for header in headers_to_test:
            custom_headers = dict(self.session.headers)
            custom_headers[header] = payload
            
            try:
                response = self.session.get(url, headers=custom_headers, timeout=10)
                status_code = response.status_code
                
                if payload in response.text:
                    vuln_info = {
                        'url': url,
                        'method': 'GET',
                        'parameter': f'Header:{header}',
                        'payload': payload,
                        'status_code': status_code
                    }
                    self.vulnerabilities.append(vuln_info)
                    print(f"\n{Fore.RED}[💀 VULNERABLE] {url}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}  ├─ Method: Header Injection | Header: {header} | Status: {status_code}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}  └─ Payload: {payload[:60]}{'...' if len(payload) > 60 else ''}{Style.RESET_ALL}\n")
                    return True
                    
            except requests.exceptions.RequestException:
                pass
                
        return False
    
    def scan(self):
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Starting XSS vulnerability scan...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        total_tests = len(self.urls) * len(self.payloads)
        current_test = 0
        url_count = 0
        
        for url in self.urls:
            url_count += 1
            print(f"\n{Fore.MAGENTA}{'─'*70}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}[>] Target [{url_count}/{len(self.urls)}]: {url}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'─'*70}{Style.RESET_ALL}")
            
            for payload in self.payloads:
                current_test += 1
                self.progress_bar(current_test, total_tests, f"Testing {current_test}/{total_tests}")
                
                self.test_reflected_xss_get(url, payload)
                self.test_reflected_xss_post(url, payload)
                self.test_header_xss(url, payload)
        
        print(f"\n{Fore.CYAN}[+] Scanning complete!{Style.RESET_ALL}\n")
        self.generate_report()
    
    def generate_report(self):
        self.spinner_active = True
        spinner_thread = threading.Thread(target=self.spinner_animation, args=("Generating report...",))
        spinner_thread.start()
        time.sleep(1)
        self.spinner_active = False
        spinner_thread.join()
        
        print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Scan Complete!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
        
        if self.vulnerabilities:
            print(f"{Fore.RED}[!] Found {len(self.vulnerabilities)} vulnerabilities!{Style.RESET_ALL}\n")
            
            with open(self.output_file, 'w') as f:
                f.write("Devil_Xss - XSS Vulnerability Report\n")
                f.write("="*70 + "\n")
                f.write(f"Developed by: S.Tamilselvan\n")
                f.write(f"GitHub: https://github.com/Tamilselvan-S-Cyber-Security\n")
                f.write(f"Official Site: https://tamilselvan-official.web.app/\n")
                f.write("="*70 + "\n\n")
                f.write(f"Total Vulnerabilities Found: {len(self.vulnerabilities)}\n\n")
                
                for i, vuln in enumerate(self.vulnerabilities, 1):
                    f.write(f"Vulnerability #{i}\n")
                    f.write(f"  URL: {vuln['url']}\n")
                    f.write(f"  Method: {vuln['method']}\n")
                    f.write(f"  Parameter: {vuln['parameter']}\n")
                    f.write(f"  Payload: {vuln['payload']}\n")
                    f.write(f"  Status Code: {vuln['status_code']}\n")
                    f.write("-"*70 + "\n")
                    
            print(f"{Fore.GREEN}[+] Report saved to: {Fore.YELLOW}{self.output_file}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[i] Total vulnerabilities found: {Fore.RED}{len(self.vulnerabilities)}{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.GREEN}[+] No vulnerabilities found. All tested URLs appear safe.{Style.RESET_ALL}\n")
            
            with open(self.output_file, 'w') as f:
                f.write("Devil_Xss - XSS Vulnerability Report\n")
                f.write("="*70 + "\n")
                f.write(f"Developed by: S.Tamilselvan\n")
                f.write(f"GitHub: https://github.com/Tamilselvan-S-Cyber-Security\n")
                f.write(f"Official Site: https://tamilselvan-official.web.app/\n")
                f.write("="*70 + "\n\n")
                f.write("No vulnerabilities found. All tested URLs appear safe.\n")

def main():
    print(ASCII_ART)
    
    parser = argparse.ArgumentParser(
        description='Devil_Xss - XSS Vulnerability Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-f', '--file', required=True, help='File containing list of URLs to test')
    parser.add_argument('-p', '--payloads', required=True, help='File containing XSS payloads')
    parser.add_argument('-o', '--output', required=True, help='Output file for vulnerable URLs')
    
    args = parser.parse_args()
    
    scanner = DevilXSS(args.file, args.payloads, args.output)
    scanner.load_urls()
    scanner.load_payloads()
    scanner.scan()

if __name__ == '__main__':
    main()
