#!/usr/bin/env python3

import requests
import argparse
import sys
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote, quote
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
import queue
import os
import html
import urllib.parse

init(autoreset=True)

ASCII_ART = f"""{Fore.RED}
 _______                        __  __         __    __                    
/       \                      /  |/  |       /  |  /  |                   
$$$$$$$  |  ______   __     __ $$/ $$ |       $$ |  $$ |  _______  _______ 
$$ |  $$ | /      \ /  \   /  |/  |$$ |       $$  \/$$/  /       |/       |
$$ |  $$ |/$$$$$$  |$$  \ /$$/ $$ |$$ |        $$  $$<  /$$$$$$$//$$$$$$$/ 
$$ |  $$ |$$    $$ | $$  /$$/  $$ |$$ |         $$$$  \ $$      \$$      \ 
$$ |__$$ |$$$$$$$$/   $$ $$/   $$ |$$ |        $$ /$$  | $$$$$$  |$$$$$$  |
$$    $$/ $$       |   $$$/    $$ |$$ |______ $$ |  $$ |/     $$//     $$/ 
$$$$$$$/   $$$$$$$/     $/     $$/ $$//      |$$/   $$/ $$$$$$$/ $$$$$$$/  
                                      $$$$$$/                              
                                                                           
                                                                           
{Style.RESET_ALL}
{Fore.CYAN}        XSS Vulnerability Scanner - Find All XSS Vulnerabilities{Style.RESET_ALL}
{Fore.YELLOW}        Developed by: S.Tamilselvan{Style.RESET_ALL}
{Fore.GREEN}        GitHub: https://github.com/Tamilselvan-S-Cyber-Security{Style.RESET_ALL}
{Fore.MAGENTA}        Official Site: https://tamilselvan-official.web.app/{Style.RESET_ALL}
{Fore.WHITE}        ================================================================{Style.RESET_ALL}
"""

class DevilXSS:
    def __init__(self, urls_file, payloads_file, output_file, threads=10):
        self.urls_file = urls_file
        self.payloads_file = payloads_file
        self.output_file = output_file
        self.threads = threads
        self.urls = []
        self.payloads = []
        self.vulnerabilities = []
        self.vulnerabilities_lock = threading.Lock()
        self.results_queue = queue.Queue()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Configure session for better performance
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=1
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.spinner_active = False
        self.spinner_chars = ['|', '/', '-', '\\\\', '|', '/', '-', '\\\\', '|', '/']
        self.total_tests = 0
        self.completed_tests = 0
        self.start_time = None
        
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
        bar = '#' * block + '.' * (bar_length - block)
        percentage = progress * 100
        
        # Calculate elapsed time and ETA
        if self.start_time:
            elapsed = time.time() - self.start_time
            if current > 0:
                eta = (elapsed / current) * (total - current)
                eta_str = f"ETA: {int(eta//60)}m{int(eta%60)}s" if eta > 60 else f"ETA: {int(eta)}s"
            else:
                eta_str = "ETA: --"
        else:
            eta_str = "ETA: --"
        
        sys.stdout.write(f'\r{Fore.CYAN}[{bar}] {percentage:.1f}% {message} | {eta_str}{Style.RESET_ALL}')
        sys.stdout.flush()
        if current == total:
            print()
    
    def display_vulnerability(self, vuln_info):
        """Display vulnerability immediately when found with enhanced details"""
        with self.vulnerabilities_lock:
            self.vulnerabilities.append(vuln_info)
        
        # Severity color coding
        severity_colors = {
            'HIGH': Fore.RED,
            'MEDIUM': Fore.YELLOW,
            'LOW': Fore.GREEN
        }
        severity_color = severity_colors.get(vuln_info.get('severity', 'LOW'), Fore.WHITE)
        
        print(f"\n{Fore.RED}[💀 VULNERABILITY FOUND!]{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  ├─ URL: {vuln_info['url']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  ├─ Method: {vuln_info['method']} | Param: {vuln_info['parameter']} | Status: {vuln_info['status_code']}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}  ├─ Payload: {vuln_info['payload'][:80]}{'...' if len(vuln_info['payload']) > 80 else ''}{Style.RESET_ALL}")
        
        # Show severity
        if 'severity' in vuln_info:
            print(f"{severity_color}  ├─ Severity: {vuln_info['severity']}{Style.RESET_ALL}")
        
        # Show encoding information
        if 'encodings' in vuln_info:
            encoding_str = ', '.join(vuln_info['encodings'])
            print(f"{Fore.BLUE}  ├─ Encoding: {encoding_str}{Style.RESET_ALL}")
        
        # Show reflection context
        if 'reflection_context' in vuln_info and vuln_info['reflection_context'] != "Context not available":
            context = vuln_info['reflection_context'][:100]
            print(f"{Fore.WHITE}  ├─ Context: ...{context}...{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}  └─ Total Found: {len(self.vulnerabilities)}{Style.RESET_ALL}\n")
        
        # Save to file immediately
        self.save_vulnerability_to_file(vuln_info)
    
    def detect_payload_encoding(self, response_text, payload):
        """Detect how the payload appears in the response"""
        encodings = []
        
        # Check for original payload
        if payload in response_text:
            encodings.append("Original")
        
        # Check for URL encoded
        url_encoded = urllib.parse.quote(payload)
        if url_encoded in response_text:
            encodings.append("URL Encoded")
        
        # Check for double URL encoded
        double_encoded = urllib.parse.quote(url_encoded)
        if double_encoded in response_text:
            encodings.append("Double URL Encoded")
        
        # Check for HTML encoded
        html_encoded = html.escape(payload)
        if html_encoded in response_text:
            encodings.append("HTML Encoded")
        
        # Check for partial encoding
        partial_encoded = payload.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        if partial_encoded in response_text:
            encodings.append("Partial HTML Encoded")
        
        # Check for JavaScript encoded
        js_encoded = payload.replace('"', '\\"').replace("'", "\\'")
        if js_encoded in response_text:
            encodings.append("JavaScript Escaped")
        
        return encodings if encodings else ["Not Found"]

    def save_vulnerability_to_file(self, vuln_info):
        """Save vulnerability to file immediately with enhanced details"""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] VULNERABILITY FOUND\n")
                f.write("=" * 100 + "\n")
                f.write(f"VULNERABLE URL: {vuln_info['url']}\n")
                f.write(f"METHOD: {vuln_info['method']}\n")
                f.write(f"PARAMETER: {vuln_info['parameter']}\n")
                f.write(f"STATUS CODE: {vuln_info['status_code']}\n")
                f.write(f"PAYLOAD: {vuln_info['payload']}\n")
                
                # Add severity information
                if 'severity' in vuln_info:
                    f.write(f"SEVERITY: {vuln_info['severity']}\n")
                
                # Add encoding information if available
                if 'encodings' in vuln_info:
                    f.write(f"ENCODING DETECTED: {', '.join(vuln_info['encodings'])}\n")
                
                # Add reflection context
                if 'reflection_context' in vuln_info and vuln_info['reflection_context'] != "Context not available":
                    f.write(f"REFLECTION CONTEXT: {vuln_info['reflection_context']}\n")
                
                # Add URL breakdown
                parsed_url = urlparse(vuln_info['url'])
                f.write(f"SCHEME: {parsed_url.scheme}\n")
                f.write(f"HOST: {parsed_url.netloc}\n")
                f.write(f"PATH: {parsed_url.path}\n")
                f.write(f"QUERY: {parsed_url.query}\n")
                
                # Decode URL parameters for better readability
                if parsed_url.query:
                    query_params = parse_qs(parsed_url.query)
                    f.write("DECODED PARAMETERS:\n")
                    for param, values in query_params.items():
                        for value in values:
                            decoded_value = unquote(value)
                            f.write(f"  {param}: {value}")
                            if decoded_value != value:
                                f.write(f" (decoded: {decoded_value})")
                            f.write("\n")
                
                # Add working script for browser testing
                f.write("BROWSER TEST URL:\n")
                f.write(f"  {vuln_info['url']}\n")
                
                f.write("-" * 100 + "\n\n")
        except Exception as e:
            print(f"{Fore.RED}[!] Error saving vulnerability: {e}{Style.RESET_ALL}")
        
    def is_testable_url(self, url):
        """Check if URL is suitable for XSS testing"""
        # Skip static resources
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot']
        if any(url.lower().endswith(ext) for ext in static_extensions):
            return False
        
        # Skip font URLs
        if 'fonts.googleapis.com' in url or 'fonts.gstatic.com' in url:
            return False
            
        # Skip CDN URLs that are likely static
        if any(cdn in url for cdn in ['cdn.', 'static.', 'assets.']):
            return False
            
        return True

    def load_urls(self):
        try:
            self.spinner_active = True
            spinner_thread = threading.Thread(target=self.spinner_animation, args=("Loading URLs...",))
            spinner_thread.start()
            
            time.sleep(0.5)
            with open(self.urls_file, 'r') as f:
                all_urls = [line.strip() for line in f if line.strip()]
            
            # Filter out non-testable URLs
            self.urls = [url for url in all_urls if self.is_testable_url(url)]
            skipped_count = len(all_urls) - len(self.urls)
            
            self.spinner_active = False
            spinner_thread.join()
            print(f"{Fore.GREEN}[+] Loaded {len(self.urls)} testable URLs successfully{Style.RESET_ALL}")
            if skipped_count > 0:
                print(f"{Fore.YELLOW}[!] Skipped {skipped_count} static resource URLs (CSS, JS, images, fonts){Style.RESET_ALL}")
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
                all_payloads = [line.strip() for line in f if line.strip()]
            
            # Filter out empty or invalid payloads
            self.payloads = [payload for payload in all_payloads if payload and len(payload) > 1]
            skipped_count = len(all_payloads) - len(self.payloads)
            
            self.spinner_active = False
            spinner_thread.join()
            print(f"{Fore.GREEN}[+] Loaded {len(self.payloads)} XSS payloads successfully{Style.RESET_ALL}")
            if skipped_count > 0:
                print(f"{Fore.YELLOW}[!] Skipped {skipped_count} empty or invalid payloads{Style.RESET_ALL}")
        except FileNotFoundError:
            self.spinner_active = False
            print(f"{Fore.RED}[!] Payloads file not found: {self.payloads_file}{Style.RESET_ALL}")
            sys.exit(1)
            
    def get_enhanced_test_parameters(self, url):
        """Get comprehensive test parameters based on URL analysis"""
        parsed_url = urlparse(url)
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        # Base parameters
        base_params = {
            'q': 'search_query',
            'search': 'search_term', 
            'query': 'search_query',
            's': 'search',
            'id': '123',
            'page': '1',
            'category': 'test',
            'type': 'search',
            'filter': 'all',
            'sort': 'relevance',
            'limit': '10',
            'offset': '0'
        }
        
        # Add path-based parameters
        if 'search' in path_parts:
            base_params.update({
                'keyword': 'test',
                'term': 'search',
                'text': 'query'
            })
        if 'user' in path_parts or 'profile' in path_parts:
            base_params.update({
                'username': 'testuser',
                'name': 'testname',
                'email': 'test@example.com'
            })
        if 'product' in path_parts or 'item' in path_parts:
            base_params.update({
                'product_id': '123',
                'item': 'testitem',
                'price': '100'
            })
            
        return base_params

    def test_reflected_xss_get(self, url, payload):
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        
        # Get enhanced test parameters
        if not params:
            test_params = self.get_enhanced_test_parameters(url)
            # Convert to payload format
            test_params = {k: payload for k, v in test_params.items()}
        else:
            test_params = {}
            for param_name in params.keys():
                test_params[param_name] = payload
        
        for param_name, test_payload in test_params.items():
            new_params = params.copy() if params else {}
            new_params[param_name] = test_payload
            
            new_query = urlencode(new_params, doseq=True)
            test_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            try:
                response = self.session.get(test_url, timeout=5, allow_redirects=True)
                status_code = response.status_code
                
                # Enhanced payload detection
                if self.is_payload_reflected(response.text, test_payload):
                    encodings = self.detect_payload_encoding(response.text, test_payload)
                    severity = self.assess_payload_severity(test_payload)
                    vuln_info = {
                        'url': test_url,
                        'method': 'GET',
                        'parameter': param_name,
                        'payload': test_payload,
                        'status_code': status_code,
                        'encodings': encodings,
                        'severity': severity,
                        'reflection_context': self.get_reflection_context(response.text, test_payload)
                    }
                    self.display_vulnerability(vuln_info)
                    return True
                    
            except requests.exceptions.RequestException:
                pass
                
        return False

    def is_payload_reflected(self, response_text, payload):
        """Enhanced payload reflection detection"""
        # Check for exact match
        if payload in response_text:
            return True
        
        # Check for URL decoded version
        decoded_payload = urllib.parse.unquote(payload)
        if decoded_payload != payload and decoded_payload in response_text:
            return True
            
        # Check for HTML decoded version
        html_decoded = html.unescape(payload)
        if html_decoded != payload and html_decoded in response_text:
            return True
            
        return False

    def assess_payload_severity(self, payload):
        """Assess the severity of a payload"""
        high_severity = ['<script', 'javascript:', 'onload=', 'onerror=', 'onclick=']
        medium_severity = ['<img', '<svg', '<iframe', 'onmouseover=', 'onfocus=']
        
        payload_lower = payload.lower()
        
        if any(high in payload_lower for high in high_severity):
            return "HIGH"
        elif any(med in payload_lower for med in medium_severity):
            return "MEDIUM"
        else:
            return "LOW"

    def get_reflection_context(self, response_text, payload):
        """Get context around payload reflection"""
        try:
            index = response_text.find(payload)
            if index != -1:
                start = max(0, index - 50)
                end = min(len(response_text), index + len(payload) + 50)
                context = response_text[start:end]
                return context.replace('\n', ' ').replace('\r', ' ').strip()
        except:
            pass
        return "Context not available"
    
    def test_reflected_xss_post(self, url, payload):
        try:
            response = self.session.get(url, timeout=5)
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
                            resp = self.session.post(form_url, data=form_data, timeout=5)
                        else:
                            resp = self.session.get(form_url, params=form_data, timeout=5)
                        
                        status_code = resp.status_code
                        
                        if payload in resp.text:
                            encodings = self.detect_payload_encoding(resp.text, payload)
                            vuln_info = {
                                'url': form_url,
                                'method': form_details['method'].upper(),
                                'parameter': input_name,
                                'payload': payload,
                                'status_code': status_code,
                                'encodings': encodings
                            }
                            self.display_vulnerability(vuln_info)
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
                response = self.session.get(url, headers=custom_headers, timeout=5)
                status_code = response.status_code
                
                if payload in response.text:
                    encodings = self.detect_payload_encoding(response.text, payload)
                    vuln_info = {
                        'url': url,
                        'method': 'GET',
                        'parameter': f'Header:{header}',
                        'payload': payload,
                        'status_code': status_code,
                        'encodings': encodings
                    }
                    self.display_vulnerability(vuln_info)
                    return True
                    
            except requests.exceptions.RequestException:
                pass
                
        return False
    
    def test_encoded_payloads(self, url, payload):
        """Test URL-encoded versions of payloads"""
        try:
            # Test URL-encoded payload
            url_encoded_payload = urllib.parse.quote(payload)
            self.test_reflected_xss_get(url, url_encoded_payload)
            
            # Test double URL-encoded payload
            double_encoded_payload = urllib.parse.quote(url_encoded_payload)
            self.test_reflected_xss_get(url, double_encoded_payload)
            
        except Exception as e:
            pass  # Silently continue on errors

    def test_single_combination(self, url, payload):
        """Test a single URL-payload combination"""
        try:
            # Test GET parameters
            self.test_reflected_xss_get(url, payload)
            # Test POST forms
            self.test_reflected_xss_post(url, payload)
            # Test headers
            self.test_header_xss(url, payload)
            # Test encoded payloads
            self.test_encoded_payloads(url, payload)
        except Exception as e:
            pass  # Silently continue on errors
        
        # Update progress
        with self.vulnerabilities_lock:
            self.completed_tests += 1
            self.progress_bar(self.completed_tests, self.total_tests, 
                            f"Testing {self.completed_tests}/{self.total_tests} | Found: {len(self.vulnerabilities)}")
    
    def scan(self):
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Starting FAST XSS vulnerability scan...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Using {self.threads} threads for maximum speed{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Results will be shown in real-time as found{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        # Store scan start time
        self.scan_start_time = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Initialize output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("Devil_Xss - XSS Vulnerability Report\n")
            f.write("="*70 + "\n")
            f.write(f"Developed by: S.Tamilselvan\n")
            f.write(f"GitHub: https://github.com/Tamilselvan-S-Cyber-Security\n")
            f.write(f"Official Site: https://tamilselvan-official.web.app/\n")
            f.write("="*70 + "\n\n")
            f.write(f"Scan started at: {self.scan_start_time}\n")
            f.write(f"URLs to test: {len(self.urls)}\n")
            f.write(f"Payloads to test: {len(self.payloads)}\n")
            f.write(f"Total combinations: {len(self.urls) * len(self.payloads)}\n")
            f.write(f"Threads: {self.threads}\n\n")
        
        # Create all URL-payload combinations
        test_combinations = []
        for url in self.urls:
            for payload in self.payloads:
                test_combinations.append((url, payload))
        
        self.total_tests = len(test_combinations)
        self.completed_tests = 0
        self.start_time = time.time()
        
        print(f"{Fore.GREEN}[+] Testing {len(self.urls)} URLs with {len(self.payloads)} payloads{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Total combinations: {self.total_tests}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Using {self.threads} threads for maximum speed{Style.RESET_ALL}\n")
        
        # Use ThreadPoolExecutor for concurrent testing
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # Submit all tasks
            futures = [executor.submit(self.test_single_combination, url, payload) 
                      for url, payload in test_combinations]
            
            # Wait for completion
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    pass  # Continue on errors
        
        print(f"\n{Fore.CYAN}[+] Scanning complete!{Style.RESET_ALL}\n")
        self.generate_report()
    
    def generate_report(self):
        # Add final summary and working scripts section to the report file
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(f"\nScan completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total vulnerabilities found: {len(self.vulnerabilities)}\n")
            f.write("="*100 + "\n\n")
            
            if self.vulnerabilities:
                # Vulnerability statistics
                severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
                method_counts = {}
                parameter_counts = {}
                
                for vuln in self.vulnerabilities:
                    severity = vuln.get('severity', 'LOW')
                    severity_counts[severity] += 1
                    
                    method = vuln.get('method', 'UNKNOWN')
                    method_counts[method] = method_counts.get(method, 0) + 1
                    
                    param = vuln.get('parameter', 'UNKNOWN')
                    parameter_counts[param] = parameter_counts.get(param, 0) + 1
                
                # Write statistics
                f.write("VULNERABILITY STATISTICS:\n")
                f.write("="*100 + "\n")
                f.write(f"Total Vulnerabilities: {len(self.vulnerabilities)}\n")
                f.write(f"High Severity: {severity_counts['HIGH']}\n")
                f.write(f"Medium Severity: {severity_counts['MEDIUM']}\n")
                f.write(f"Low Severity: {severity_counts['LOW']}\n\n")
                
                f.write("METHOD DISTRIBUTION:\n")
                for method, count in method_counts.items():
                    f.write(f"  {method}: {count}\n")
                f.write("\n")
                
                f.write("TOP PARAMETERS:\n")
                sorted_params = sorted(parameter_counts.items(), key=lambda x: x[1], reverse=True)
                for param, count in sorted_params[:10]:  # Top 10
                    f.write(f"  {param}: {count}\n")
                f.write("\n")
                
                # Working scripts section
                f.write("WORKING SCRIPTS - COPY & PASTE INTO BROWSER:\n")
                f.write("="*100 + "\n\n")
                
                for i, vuln in enumerate(self.vulnerabilities, 1):
                    severity = vuln.get('severity', 'LOW')
                    f.write(f"{i}. [{severity}] {vuln['url']}\n")
                    f.write(f"   Method: {vuln['method']}\n")
                    f.write(f"   Parameter: {vuln['parameter']}\n")
                    f.write(f"   Payload: {vuln['payload']}\n")
                    if 'encodings' in vuln:
                        f.write(f"   Encoding: {', '.join(vuln['encodings'])}\n")
                    f.write("\n")
                
                f.write("="*100 + "\n")
                f.write("SCAN SUMMARY:\n")
                f.write("="*100 + "\n")
                f.write(f"Scan started at: {self.scan_start_time}\n")
                f.write(f"URLs to test: {len(self.urls)}\n")
                f.write(f"Payloads to test: {len(self.payloads)}\n")
                f.write(f"Total combinations: {len(self.urls) * len(self.payloads)}\n")
                f.write(f"Threads: {self.threads}\n\n")
                f.write(f"Scan completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total vulnerabilities found: {len(self.vulnerabilities)}\n")
                f.write("="*100 + "\n")
        
        print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Scan Complete!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
        
        if self.vulnerabilities:
            # Show vulnerability statistics
            severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            for vuln in self.vulnerabilities:
                severity = vuln.get('severity', 'LOW')
                severity_counts[severity] += 1
            
            print(f"{Fore.RED}[!] Found {len(self.vulnerabilities)} vulnerabilities!{Style.RESET_ALL}")
            print(f"{Fore.RED}  ├─ High Severity: {severity_counts['HIGH']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  ├─ Medium Severity: {severity_counts['MEDIUM']}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  └─ Low Severity: {severity_counts['LOW']}{Style.RESET_ALL}\n")
            
            print(f"{Fore.GREEN}[+] Report saved to: {Fore.YELLOW}{self.output_file}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[i] Total vulnerabilities found: {Fore.RED}{len(self.vulnerabilities)}{Style.RESET_ALL}\n")
            
            # Show working scripts in console
            print(f"{Fore.YELLOW}WORKING SCRIPTS - COPY & PASTE INTO BROWSER:{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            for i, vuln in enumerate(self.vulnerabilities[:10], 1):  # Show first 10
                severity = vuln.get('severity', 'LOW')
                severity_color = {'HIGH': Fore.RED, 'MEDIUM': Fore.YELLOW, 'LOW': Fore.GREEN}.get(severity, Fore.WHITE)
                print(f"{Fore.CYAN}{i}. {vuln['url']}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}   Method: {vuln['method']} | Param: {vuln['parameter']} | {severity_color}Severity: {severity}{Style.RESET_ALL}")
                print(f"{Fore.MAGENTA}   Payload: {vuln['payload']}{Style.RESET_ALL}\n")
            
            if len(self.vulnerabilities) > 10:
                print(f"{Fore.CYAN}... and {len(self.vulnerabilities) - 10} more vulnerabilities (see full report){Style.RESET_ALL}\n")
        else:
            print(f"{Fore.GREEN}[+] No vulnerabilities found. All tested URLs appear safe.{Style.RESET_ALL}\n")
            print(f"{Fore.GREEN}[+] Report saved to: {Fore.YELLOW}{self.output_file}{Style.RESET_ALL}\n")

def main():
    print(ASCII_ART)
    
    parser = argparse.ArgumentParser(
        description='Devil_Xss - FAST XSS Vulnerability Scanner with Real-time Results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python devil_xss.py -f urls.txt -p payloads.txt -o results.txt
  python devil_xss.py -f urls.txt -p payloads.txt -o results.txt -t 20
  python devil_xss.py -f urls.txt -p payloads.txt -o results.txt -t 50 --fast
        """
    )
    
    parser.add_argument('-f', '--file', required=True, help='File containing list of URLs to test')
    parser.add_argument('-p', '--payloads', required=True, help='File containing XSS payloads')
    parser.add_argument('-o', '--output', required=True, help='Output file for vulnerable URLs')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Number of threads to use (default: 10)')
    parser.add_argument('--fast', action='store_true', help='Use maximum threads (50) for fastest scanning')
    
    args = parser.parse_args()
    
    # Adjust thread count for fast mode
    if args.fast:
        args.threads = min(50, os.cpu_count() * 4)
        print(f"{Fore.YELLOW}[!] Fast mode enabled - Using {args.threads} threads{Style.RESET_ALL}")
    
    scanner = DevilXSS(args.file, args.payloads, args.output, args.threads)
    scanner.load_urls()
    scanner.load_payloads()
    scanner.scan()

if __name__ == '__main__':
    main()
