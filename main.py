import os
import re
import requests
from colorama import init, Fore, Style
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import tzlocal
import time
from urllib.parse import urlparse
from web3 import Web3

init(autoreset=True)

# CONFIGURATION
THREADS = 10  # Number of concurrent wallets
CAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY"  # Your 2Captcha API key
MAX_RETRIES = 10  # Max retries for failed attempts
DELAY_BETWEEN_BATCHES = 10  # Delay between wallet batches in seconds

# Blockchain configuration for balance checking
RPC_URL = "https://0g-evm-rpc.murphynode.net"
CHAIN_ID = 16600
SYMBOL = "A0GI"

# hCaptcha configuration
HCAPTCHA_SITEKEY = "914e63b4-ac20-4c24-bc92-cdb6950ccfde"
HCAPTCHA_PAGE_URL = "https://faucet.0g.ai"

# File paths
WALLETS_FILE = "wallets.txt"
PROXIES_FILE = "proxies.txt"
FAUCET_API_URL = "https://faucet.0g.ai/api/faucet"

headers = {"Content-Type": "application/json"}

# Cache system
PROXY_CACHE = {}
CACHE_LOCK = threading.Lock()

# Initialize Web3 connection
web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    log_fail("Failed to connect to 0G-Newton-Testnet network")

def now_local():
    """Get current local time"""
    tz = tzlocal.get_localzone()
    return datetime.now(tz).strftime("%H:%M:%S %d/%m/%Y")

def log_info(msg, idx=None):
    prefix = f"[{now_local()}] [{idx}]" if idx is not None else f"[{now_local()}]"
    print(f"{Fore.CYAN}{prefix} {msg}{Style.RESET_ALL}")

def log_success(msg, idx=None):
    prefix = f"[{now_local()}] [{idx}]" if idx is not None else f"[{now_local()}]"
    print(f"{Fore.GREEN}{prefix} {msg}{Style.RESET_ALL}")

def log_fail(msg, idx=None):
    prefix = f"[{now_local()}] [{idx}]" if idx is not None else f"[{now_local()}]"
    print(f"{Fore.RED}{prefix} {msg}{Style.RESET_ALL}")

def log_warning(msg, idx=None):
    prefix = f"[{now_local()}] [{idx}]" if idx is not None else f"[{now_local()}]"
    print(f"{Fore.YELLOW}{prefix} {msg}{Style.RESET_ALL}")

def parse_proxy(proxy_str):
    """Parse proxy string into proper format"""
    try:
        if not proxy_str:
            return None
            
        if '://' in proxy_str:
            parsed = urlparse(proxy_str)
            scheme = parsed.scheme
            netloc = parsed.netloc
            
            if '@' in netloc:
                auth, hostport = netloc.split('@', 1)
                user, pwd = auth.split(':', 1)
                host, port = hostport.split(':', 1)
                if scheme in ['http', 'https']:
                    return f"{scheme}://{user}:{pwd}@{host}:{port}"
                elif scheme == 'socks5':
                    return f"socks5://{user}:{pwd}@{host}:{port}"
            else:
                host, port = netloc.split(':', 1)
                if scheme in ['http', 'https']:
                    return f"{scheme}://{host}:{port}"
                elif scheme == 'socks5':
                    return f"socks5://{host}:{port}"
        else:
            parts = proxy_str.split(':')
            if len(parts) == 4:
                host, port, user, pwd = parts
                return f"http://{user}:{pwd}@{host}:{port}"
            elif len(parts) == 2:
                host, port = parts
                return f"http://{host}:{port}"
        
        log_warning(f"Unrecognized proxy format: {proxy_str}")
        return None
    except Exception as e:
        log_warning(f"Error parsing proxy {proxy_str}: {str(e)}")
        return None

# Load proxies
try:
    with open(PROXIES_FILE, "r") as f:
        proxies_list = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    proxies_list = []
    log_warning("proxies.txt not found, running without proxies")

proxy_index = 0
PROXY_LOCK = threading.Lock()

def get_next_proxy():
    """Get next proxy in rotation"""
    global proxy_index
    with PROXY_LOCK:
        if not proxies_list:
            return None
            
        proxy_str = proxies_list[proxy_index % len(proxies_list)]
        proxy_index += 1
        return parse_proxy(proxy_str)

def get_current_ip(proxy, idx=None):
    """Get current IP with minimal data usage"""
    try:
        if not proxy:
            return "No proxy"
        
        # Check cache first
        with CACHE_LOCK:
            if proxy in PROXY_CACHE:
                return PROXY_CACHE[proxy]
        
        # Use lightweight IP check service
        proxies = {"http": proxy, "https": proxy}
        r = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
        
        if r.status_code == 200:
            ip = r.json().get("origin", "Unknown IP")
            # Store in cache
            with CACHE_LOCK:
                PROXY_CACHE[proxy] = ip
            return ip
        return f"IP check failed - Status {r.status_code}"
    except Exception as e:
        log_fail(f"Error getting IP: {str(e)}", idx=idx)
        return "Error"

def get_captcha_id(apikey, proxy=None, idx=None):
    """Get captcha ID from 2Captcha service"""
    try:
        url = "http://2captcha.com/in.php"
        payload = {
            "key": apikey,
            "method": "hcaptcha",
            "sitekey": HCAPTCHA_SITEKEY,
            "pageurl": HCAPTCHA_PAGE_URL,
            "json": 1
        }
        
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.post(url, json=payload, proxies=proxies, timeout=30)
        result = response.json()
        
        if result.get("status") == 1:
            return result.get("request")
        else:
            log_fail(f"2Captcha error: {result.get('error_text', 'Unknown error')}", idx=idx)
            return None
    except Exception as e:
        log_fail(f"Error getting captcha ID: {str(e)}", idx=idx)
        return None

def get_captcha_token(apikey, captcha_id, proxy=None, idx=None):
    """Get solved captcha token from 2Captcha"""
    try:
        url = f"http://2captcha.com/res.php?key={apikey}&action=get&id={captcha_id}&json=1"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.get(url, proxies=proxies, timeout=30)
        result = response.json()
        
        if result.get("status") == 1:
            return result.get("request")
        elif result.get("request") == "CAPCHA_NOT_READY":
            return "CAPCHA_NOT_READY"
        else:
            log_fail(f"2Captcha error: {result.get('error_text', 'Unknown error')}", idx=idx)
            return None
    except Exception as e:
        log_fail(f"Error getting captcha token: {str(e)}", idx=idx)
        return None

def solve_hcaptcha(idx=None):
    """Solve hCaptcha challenge using 2Captcha"""
    try:
        proxy = get_next_proxy()
        ip_info = get_current_ip(proxy, idx=idx)
        log_info(f"Using proxy: {ip_info}", idx=idx)

        captcha_id = get_captcha_id(CAPTCHA_API_KEY, proxy, idx)
        
        if not captcha_id:
            log_fail("Failed to get captcha ID", idx=idx)
            return None
            
        log_info(f"Captcha ID: {captcha_id}", idx=idx)
        
        max_attempts = 60
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            token_response = get_captcha_token(CAPTCHA_API_KEY, captcha_id, proxy, idx)
            
            if not token_response:
                log_info(f"Waiting for captcha... (attempt {attempt}/{max_attempts})", idx=idx)
                time.sleep(2)
                continue
                
            if token_response == "CAPCHA_NOT_READY":
                if attempt % 5 == 0:
                    log_info(f"Captcha not ready yet... (attempt {attempt}/{max_attempts})", idx=idx)
                time.sleep(2)
                continue
            else:
                log_success("Successfully solved captcha", idx=idx)
                return token_response
                
        log_fail("Captcha timeout", idx=idx)
        return None
    except Exception as e:
        log_fail(f"Error solving captcha: {str(e)}", idx=idx)
        return None

def faucet_claim(wallet, token, proxy, idx=None):
    """Claim from faucet"""
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.post(
            FAUCET_API_URL,
            json={"address": wallet, "hcaptchaToken": token},
            headers=headers,
            proxies=proxies,
            timeout=300
        )
        return resp.json()
    except Exception as e:
        log_fail(f"Error claiming faucet: {str(e)}", idx=idx)
        return {'message': 'Connection error'}

def check_balance(wallet, idx=None):
    """Check wallet balance"""
    try:
        wallet = Web3.to_checksum_address(wallet)
        balance = web3.eth.get_balance(wallet)
        balance_a0gi = web3.from_wei(balance, 'ether')
        log_success(f"{wallet} - Balance {SYMBOL}: {balance_a0gi} {SYMBOL}", idx=idx)
        return float(balance_a0gi)
    except Exception as e:
        log_fail(f"Error checking balance for {wallet}: {str(e)}", idx=idx)
        return 0

def check_all_balances(wallets):
    """Check balances for all wallets"""
    log_info("Checking all wallet balances...")
    total_balance = 0
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(check_balance, wallet, i): (i, wallet) 
                  for i, wallet in enumerate(wallets, start=1)}
        
        for future in as_completed(futures):
            i, wallet = futures[future]
            try:
                balance = future.result()
                total_balance += balance
            except Exception as e:
                log_fail(f"Error processing balance check for {wallet}: {str(e)}", idx=i)
    
    log_success(f"Total balance of all wallets: {total_balance} {SYMBOL}")
    return total_balance

def process_wallet(wallet, index, stop_event):
    """Process single wallet"""
    log_info(f"Processing wallet: {wallet}", idx=index)
    attempts = 0
    max_attempts = len(proxies_list) if proxies_list else 1
    
    while attempts < max_attempts and not stop_event.is_set():
        proxy = get_next_proxy()
        if not proxy and proxies_list:
            log_fail("No proxies available", idx=index)
            break
            
        token = solve_hcaptcha(idx=index)
        if not token:
            log_fail("Failed to solve captcha", idx=index)
            attempts += 1
            time.sleep(1)
            continue

        retry_count = 0
        while retry_count < MAX_RETRIES and not stop_event.is_set():
            resp = faucet_claim(wallet, token, proxy, idx=index)
            if resp:
                msg = resp.get("message", "")
                log_info(f"Faucet response: {resp}", idx=index)
                
                # Check for success
                if (re.match(r'^0x[a-fA-F0-9]{64}$', msg) or 
                    msg == "Please wait 24 hours before requesting again"):
                    log_success(f"Successfully claimed for {wallet}", idx=index)
                    return
                
                # Check for retryable errors
                if (msg in ["Timeout. Please retry.", "Unable to Send Transaction", "Invalid Captcha"] or
                    any(err in msg.lower() for err in ["connection aborted", "closed connection", "httpsconnectionpool"]) or
                    msg == "Service is busy. Please retry later."):
                    retry_count += 1
                    log_warning(f"Retry {retry_count}/{MAX_RETRIES} for {wallet}", idx=index)
                    time.sleep(1)
                    continue
                
                # Unrecognized response
                log_fail(f"Unrecognized response: {msg}", idx=index)
                break
            else:
                log_fail("No response from faucet", idx=index)
                break
        
        attempts += 1
        time.sleep(1)

    log_fail(f"Failed to claim for {wallet} after {attempts} attempts", idx=index)

def get_wallet_files():
    """Get list of wallet files in format walletsX.txt"""
    files = []
    for file in os.listdir():
        match = re.match(r"wallets(\d+)\.txt", file)
        if match:
            files.append((int(match.group(1)), file))
    return sorted(files)

def rotate_wallet_file():
    """Rotate wallet files by moving the next one to wallets.txt"""
    wallet_files = get_wallet_files()

    if not wallet_files:
        log_warning("No more wallet files found with pattern walletsX.txt")
        return False

    # Get the file with smallest number
    smallest_number, smallest_file = wallet_files[0]

    # Read content of the next wallet file
    with open(smallest_file, "r") as src_file:
        content = src_file.read()

    # Write to wallets.txt
    with open(WALLETS_FILE, "w") as dest_file:
        dest_file.write(content)

    # Remove the source file
    os.remove(smallest_file)

    log_success(f"Rotated wallet file: {smallest_file} -> wallets.txt")
    return True

def process_wallet_batch(stop_event):
    """Process a single batch of wallets from wallets.txt"""
    try:
        with open(WALLETS_FILE, "r") as f:
            wallets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        log_fail("wallets.txt not found!")
        return False
    
    if not wallets:
        log_fail("No wallets in wallets.txt")
        return False
    
    if not proxies_list:
        log_warning("No proxies available, running without proxies")

    # Process all wallets once
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(process_wallet, wallet, i, stop_event): wallet 
                  for i, wallet in enumerate(wallets, start=1)}
        try:
            for future in as_completed(futures):
                future.result()
        except KeyboardInterrupt:
            log_info("Stopping current batch...")
            stop_event.set()
            for future in futures:
                future.cancel()
            raise

    # After completing all claims, check all balances
    if not stop_event.is_set():
        log_info("Faucet claiming completed. Checking wallet balances...")
        check_all_balances(wallets)
    
    return True

def main():
    """Main function"""
    log_info("Starting faucet claim process...")
    log_info(f"Thread count: {THREADS}")
    log_info(f"Using API key: {CAPTCHA_API_KEY}")

    stop_event = threading.Event()
    processed_files = 0

    try:
        while not stop_event.is_set():
            # Process current wallet batch
            success = process_wallet_batch(stop_event)
            
            if not success:
                break
            
            processed_files += 1
            
            # Try to rotate to next wallet file
            if not rotate_wallet_file():
                break
                
            # Add delay before processing next batch
            if not stop_event.is_set():
                log_info(f"Waiting {DELAY_BETWEEN_BATCHES} seconds before processing next wallet batch...")
                time.sleep(DELAY_BETWEEN_BATCHES)
    
    except KeyboardInterrupt:
        log_info("Program stopped by user")
    finally:
        log_success(f"Processing completed. Total wallet files processed: {processed_files}")

if __name__ == "__main__":
    main()