#!/usr/bin/env python3

import requests
import argparse
import sys
import re
import time
import threading
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed

init(autoreset=True)

ASCII_ART = f"""{Fore.CYAN}
██╗   ██╗██████╗ ██╗      ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
██║   ██║██╔══██╗██║      ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
██║   ██║██████╔╝██║█████╗█████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
██║   ██║██╔══██╗██║╚════╝██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║███████╗ ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                       
{Style.RESET_ALL}
{Fore.YELLOW}     Advanced URL Discovery Tool - Extract All URLs from Websites{Style.RESET_ALL}
{Fore.GREEN}        Developed by: S.Tamilselvan{Style.RESET_ALL}
{Fore.MAGENTA}        GitHub: https://github.com/Tamilselvan-S-Cyber-Security{Style.RESET_ALL}
{Fore.CYAN}        Official Site: https://tamilselvan-official.web.app/{Style.RESET_ALL}
{Fore.WHITE}        ================================================================{Style.RESET_ALL}
"""

class URLFinder:
    def __init__(self, target_url, output_file, depth=2, max_threads=10):
        self.target_url = target_url
        self.output_file = output_file
        self.depth = depth
        self.max_threads = max_threads
        self.found_urls = set()
        self.internal_urls = set()
        self.external_urls = set()
        self.visited_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.spinner_active = False
        self.spinner_chars = ['|', '/', '-', '\\', '|', '/', '-', '\\', '|', '/']
        self.base_domain = urlparse(target_url).netloc
        self.common_directories = [
            'admin', 'administrator', 'login', 'signin', 'register', 'signup',
            'dashboard', 'panel', 'control', 'manage', 'api', 'v1', 'v2',
            'test', 'dev', 'staging', 'beta', 'alpha', 'backup', 'backups',
            'config', 'configuration', 'settings', 'profile', 'user', 'users',
            'account', 'accounts', 'billing', 'payment', 'payments',
            'support', 'help', 'faq', 'contact', 'about', 'privacy',
            'terms', 'legal', 'security', 'docs', 'documentation',
            'blog', 'news', 'articles', 'posts', 'media', 'files',
            'uploads', 'downloads', 'assets', 'static', 'public',
            'private', 'secure', 'auth', 'oauth', 'sso', 'logout',
            'search', 'find', 'query', 'results', '404', '500',
            'error', 'errors', 'debug', 'logs', 'monitoring',
            'status', 'health', 'ping', 'metrics', 'analytics'
        ]
        self.common_files = [
            'robots.txt', 'sitemap.xml', 'sitemap_index.xml',
            'crossdomain.xml', 'clientaccesspolicy.xml',
            'favicon.ico', 'apple-touch-icon.png',
            'manifest.json', 'swagger.json', 'api.json',
            'openapi.json', 'graphql', 'graphiql',
            'phpinfo.php', 'info.php', 'test.php',
            'admin.php', 'login.php', 'wp-admin',
            'wp-login.php', 'xmlrpc.php', 'readme.txt',
            'changelog.txt', 'license.txt', 'version.txt'
        ]
        
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
        bar = '#' * block + '.' * (bar_length - block)
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
    
    def is_internal_url(self, url):
        """Check if URL belongs to the same domain"""
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain or parsed.netloc == ''
    
    def should_visit_url(self, url):
        """Check if URL should be visited for crawling"""
        if url in self.visited_urls:
            return False
        
        # Skip non-HTTP(S) URLs
        if not url.startswith(('http://', 'https://')):
            return False
            
        # Skip static resources
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.zip', '.tar', '.gz']
        if any(url.lower().endswith(ext) for ext in static_extensions):
            return False
            
        # Skip external URLs for deep crawling
        if not self.is_internal_url(url):
            return False
            
        return True
    
    def discover_sitemaps(self, base_url):
        """Discover and parse sitemaps"""
        sitemap_urls = set()
        sitemap_candidates = [
            urljoin(base_url, '/sitemap.xml'),
            urljoin(base_url, '/sitemap_index.xml'),
            urljoin(base_url, '/sitemaps.xml'),
            urljoin(base_url, '/sitemap-index.xml'),
            urljoin(base_url, '/sitemap/index.xml'),
            urljoin(base_url, '/sitemap/sitemap.xml')
        ]
        
        for sitemap_url in sitemap_candidates:
            try:
                response = self.session.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    sitemap_urls.add(sitemap_url)
                    # Parse sitemap for URLs
                    try:
                        root = ET.fromstring(response.content)
                        for url_elem in root.iter():
                            if url_elem.tag.endswith('loc'):
                                sitemap_urls.add(url_elem.text)
                            elif url_elem.tag.endswith('sitemap'):
                                for loc in url_elem:
                                    if loc.tag.endswith('loc'):
                                        sitemap_urls.add(loc.text)
                    except ET.ParseError:
                        # Try to extract URLs using regex if XML parsing fails
                        url_pattern = r'https?://[^\s<>"]+'
                        matches = re.findall(url_pattern, response.text)
                        sitemap_urls.update(matches)
            except:
                continue
                
        return sitemap_urls
    
    def discover_robots_txt(self, base_url):
        """Discover URLs from robots.txt"""
        robots_urls = set()
        robots_url = urljoin(base_url, '/robots.txt')
        
        try:
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                lines = response.text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        robots_urls.add(sitemap_url)
                    elif line.startswith('Allow:') or line.startswith('Disallow:'):
                        path = line.split(':', 1)[1].strip()
                        if path and not path.startswith('*'):
                            full_url = urljoin(base_url, path)
                            robots_urls.add(full_url)
        except:
            pass
            
        return robots_urls
    
    def discover_common_paths(self, base_url):
        """Discover common directory and file paths"""
        discovered_urls = set()
        
        # Test common directories
        for directory in self.common_directories:
            test_url = urljoin(base_url, f'/{directory}/')
            discovered_urls.add(test_url)
            
        # Test common files
        for filename in self.common_files:
            test_url = urljoin(base_url, f'/{filename}')
            discovered_urls.add(test_url)
            
        return discovered_urls
    
    def discover_api_endpoints(self, base_url):
        """Discover potential API endpoints"""
        api_urls = set()
        api_patterns = [
            '/api', '/api/v1', '/api/v2', '/api/v3',
            '/rest', '/rest/v1', '/rest/v2',
            '/graphql', '/graphiql',
            '/swagger', '/swagger-ui', '/swagger.json',
            '/openapi', '/openapi.json',
            '/docs', '/documentation',
            '/webhook', '/webhooks',
            '/callback', '/callbacks',
            '/oauth', '/oauth2',
            '/auth', '/authentication',
            '/token', '/tokens',
            '/refresh', '/revoke'
        ]
        
        for pattern in api_patterns:
            api_url = urljoin(base_url, pattern)
            api_urls.add(api_url)
            
        return api_urls
    
    def deep_crawl_url(self, url, current_depth):
        """Recursively crawl a URL to find more URLs"""
        if current_depth >= self.depth or not self.should_visit_url(url):
            return set()
            
        self.visited_urls.add(url)
        urls = set()
        
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract URLs from HTML
                for tag in soup.find_all(['a', 'link']):
                    href = tag.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        if self.is_internal_url(full_url):
                            urls.add(full_url)
                
                for tag in soup.find_all(['img', 'script', 'iframe', 'embed', 'source']):
                    src = tag.get('src')
                    if src:
                        full_url = urljoin(url, src)
                        if self.is_internal_url(full_url):
                            urls.add(full_url)
                            
        except:
            pass
            
        return urls
    
    def discover_urls(self):
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Starting DEEP URL Discovery...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Depth Level: {self.depth} | Threads: {self.max_threads}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.MAGENTA}[>] Target: {self.target_url}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}[>] Domain: {self.base_domain}{Style.RESET_ALL}\n")
        
        # Phase 1: Basic URL extraction
        print(f"{Fore.CYAN}[*] Phase 1: Basic URL Extraction{Style.RESET_ALL}")
        response = self.fetch_page(self.target_url)
        
        if not response:
            print(f"{Fore.RED}[-] Failed to fetch target URL{Style.RESET_ALL}")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        basic_tasks = [
            ("HTML elements", self.extract_urls_from_html, soup, self.target_url),
            ("JavaScript code", self.extract_urls_from_javascript, soup, self.target_url),
            ("Raw text content", self.extract_urls_from_text, response.text, self.target_url)
        ]
        
        for idx, (name, func, *args) in enumerate(basic_tasks, 1):
            self.spinner_active = True
            spinner_thread = threading.Thread(target=self.spinner_animation, args=(f"Scanning {name}...",))
            spinner_thread.start()
            
            time.sleep(0.3)
            urls = func(*args)
            
            self.spinner_active = False
            spinner_thread.join()
            
            self.found_urls.update(urls)
            print(f"{Fore.GREEN}[+] Extracted from {name}: {len(urls)} URLs{Style.RESET_ALL}")
        
        # Phase 2: Deep discovery methods
        print(f"\n{Fore.CYAN}[*] Phase 2: Deep Discovery Methods{Style.RESET_ALL}")
        
        deep_tasks = [
            ("Sitemaps", self.discover_sitemaps, self.target_url),
            ("Robots.txt", self.discover_robots_txt, self.target_url),
            ("Common paths", self.discover_common_paths, self.target_url),
            ("API endpoints", self.discover_api_endpoints, self.target_url)
        ]
        
        for idx, (name, func, *args) in enumerate(deep_tasks, 1):
            self.spinner_active = True
            spinner_thread = threading.Thread(target=self.spinner_animation, args=(f"Discovering {name}...",))
            spinner_thread.start()
            
            time.sleep(0.3)
            urls = func(*args)
            
            self.spinner_active = False
            spinner_thread.join()
            
            self.found_urls.update(urls)
            print(f"{Fore.GREEN}[+] Discovered from {name}: {len(urls)} URLs{Style.RESET_ALL}")
        
        # Phase 3: Deep crawling
        if self.depth > 1:
            print(f"\n{Fore.CYAN}[*] Phase 3: Deep Crawling (Depth: {self.depth}){Style.RESET_ALL}")
            
            # Get internal URLs for crawling
            internal_urls = [url for url in self.found_urls if self.is_internal_url(url)]
            crawl_urls = [url for url in internal_urls if self.should_visit_url(url)]
            
            print(f"{Fore.YELLOW}[*] Found {len(crawl_urls)} URLs to crawl{Style.RESET_ALL}")
            
            # Use threading for deep crawling
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = []
                for url in crawl_urls[:50]:  # Limit to prevent too many requests
                    future = executor.submit(self.deep_crawl_url, url, 1)
                    futures.append(future)
                
                completed = 0
                for future in as_completed(futures):
                    try:
                        new_urls = future.result()
                        self.found_urls.update(new_urls)
                        completed += 1
                        self.progress_bar(completed, len(futures), f"Crawling {completed}/{len(futures)}")
                    except:
                        completed += 1
                        self.progress_bar(completed, len(futures), f"Crawling {completed}/{len(futures)}")
        
        # Clean and categorize URLs
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
        print(f"{Fore.WHITE}  |-- Total URLs Found: {Fore.YELLOW}{total_urls}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  |-- Internal URLs: {Fore.GREEN}{internal_count}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  `-- External URLs: {Fore.MAGENTA}{external_count}{Style.RESET_ALL}\n")
        
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
        description='URL Finder - Advanced Deep URL Discovery Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python url_finder.py -u https://example.com -o urls.txt
  python url_finder.py -u https://example.com -o urls.txt -d 3 -t 20
  python url_finder.py -u https://example.com -o urls.txt --deep
        """
    )
    
    parser.add_argument('-u', '--url', required=True, help='Target URL to scan for URLs')
    parser.add_argument('-o', '--output', required=True, help='Output file to store discovered URLs')
    parser.add_argument('-d', '--depth', type=int, default=2, help='Crawling depth level (default: 2)')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Number of threads for deep crawling (default: 10)')
    parser.add_argument('--deep', action='store_true', help='Enable maximum depth discovery (depth=3, threads=20)')
    
    args = parser.parse_args()
    
    if not args.url.startswith(('http://', 'https://')):
        print(f"{Fore.RED}[-] Error: URL must start with http:// or https://{Style.RESET_ALL}")
        sys.exit(1)
    
    # Adjust parameters for deep mode
    if args.deep:
        args.depth = 3
        args.threads = 20
        print(f"{Fore.YELLOW}[!] Deep mode enabled - Using depth={args.depth}, threads={args.threads}{Style.RESET_ALL}")
    
    finder = URLFinder(args.url, args.output, args.depth, args.threads)
    finder.discover_urls()

if __name__ == '__main__':
    main()
