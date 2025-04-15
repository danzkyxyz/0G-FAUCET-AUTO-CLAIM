import json
import time
from web3 import Web3, exceptions
from decimal import Decimal
from colorama import init, Fore, Style
from datetime import datetime
import os

# Initialize colorama
init(autoreset=True)

# Network Configuration
RPC_URL = "https://0g-evm-rpc.murphynode.net"
CHAIN_ID = 16600
EXPLORER_URL = "https://chainscan-newton.0g.ai/tx/"
BASE_GAS_PRICE = Web3.to_wei(0.000000027, 'gwei')
GAS_LIMIT = 21000
GAS_BUMP_PERCENT = 0
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries

# File paths
PVKEY_FILE = "pvkey.txt"
WALLET_FILE = "wallet.txt"

# Connect to network
w3 = Web3(Web3.HTTPProvider(RPC_URL))

def log_info(msg):
    print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] {msg}{Style.RESET_ALL}")

def log_success(msg):
    print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] {msg}{Style.RESET_ALL}")

def log_warning(msg):
    print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] {msg}{Style.RESET_ALL}")

def log_error(msg):
    print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] {msg}{Style.RESET_ALL}")

def get_current_gas_price():
    """Get current gas price with priority bump"""
    try:
        base_price = w3.eth.gas_price
        if base_price < BASE_GAS_PRICE:
            base_price = BASE_GAS_PRICE
        return int(base_price * (1 + GAS_BUMP_PERCENT / 100))
    except:
        return BASE_GAS_PRICE

def load_private_keys():
    """Load private keys from file"""
    if not os.path.exists(PVKEY_FILE):
        log_error(f"File {PVKEY_FILE} not found!")
        return []

    with open(PVKEY_FILE, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

def load_recipient_wallets():
    """Load recipient wallets from file"""
    if not os.path.exists(WALLET_FILE):
        log_error(f"File {WALLET_FILE} not found!")
        return []

    with open(WALLET_FILE, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

def get_balance(address):
    """Get current balance of an address in ETH"""
    balance = w3.eth.get_balance(address)
    return Decimal(w3.from_wei(balance, 'ether'))

def send_amount(sender_pvkey, recipient, amount_eth, nonce):
    """Send specific amount to recipient"""
    sender_account = w3.eth.account.from_key(sender_pvkey)
    amount_wei = Web3.to_wei(amount_eth, 'ether')
    
    current_gas_price = get_current_gas_price()
    gas_cost = GAS_LIMIT * current_gas_price
    balance_wei = w3.eth.get_balance(sender_account.address)
    
    if balance_wei < amount_wei + gas_cost:
        return None, f"Insufficient balance. Required: {Web3.from_wei(amount_wei + gas_cost, 'ether'):.6f}, Available: {Web3.from_wei(balance_wei, 'ether'):.6f}"
    
    recipient = Web3.to_checksum_address(recipient)
    
    for attempt in range(MAX_RETRIES):
        try:
            tx = {
                'chainId': CHAIN_ID,
                'to': recipient,
                'value': amount_wei,
                'gas': GAS_LIMIT,
                'gasPrice': current_gas_price,
                'nonce': nonce,
            }
            
            signed_tx = w3.eth.account.sign_transaction(tx, sender_pvkey)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return tx_hash.hex(), None
        except exceptions.TransactionNotFound:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            return None, "Transaction not found"
        except ValueError as e:
            if "mempool is full" in str(e) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return None, str(e)
        except Exception as e:
            return None, str(e)

def process_wallets(private_keys, recipient_wallets, amount_per_wallet):
    """Process all wallets and send to multiple recipients"""
    results = []
    
    if not recipient_wallets:
        log_error("No recipient wallet addresses found in wallet.txt")
        return results
    
    total_recipients = len(recipient_wallets)
    amount_per_recipient = amount_per_wallet / total_recipients
    
    for idx, pvkey in enumerate(private_keys, 1):
        try:
            account = w3.eth.account.from_key(pvkey)
            current_balance = get_balance(account.address)
            nonce = w3.eth.get_transaction_count(account.address)
            
            log_info(f"Processing wallet {idx} | Balance: {current_balance:.6f} A0GI")
            log_info(f"Nonce for wallet {idx}: {nonce}")
            
            if current_balance <= 0:
                log_warning(f"Wallet {idx} has zero balance, skipped")
                results.append({
                    'wallet_index': idx,
                    'wallet_address': account.address,
                    'status': 'skipped',
                    'reason': 'zero_balance',
                    'balance': float(current_balance)
                })
                continue
            
            # Send to each recipient wallet
            for recipient_idx, recipient in enumerate(recipient_wallets, 1):
                tx_hash, error = send_amount(pvkey, recipient, amount_per_recipient, nonce)
                nonce += 1  # Increment nonce for the next transaction
                
                if tx_hash:
                    log_success(f"Wallet {idx} -> Recipient {recipient_idx}: {amount_per_recipient:.6f} A0GI | TX Hash: {EXPLORER_URL}{tx_hash}")
                    results.append({
                        'sender_index': idx,
                        'sender_address': account.address,
                        'recipient_index': recipient_idx,
                        'recipient_address': recipient,
                        'status': 'success',
                        'tx_hash': tx_hash,
                        'explorer_url': f"{EXPLORER_URL}{tx_hash}",
                        'amount_sent': float(amount_per_recipient),
                        'balance_before': float(current_balance)
                    })
                else:
                    log_error(f"Wallet {idx} -> Recipient {recipient_idx}: Failed: {error}")
                    results.append({
                        'sender_index': idx,
                        'sender_address': account.address,
                        'recipient_index': recipient_idx,
                        'recipient_address': recipient,
                        'status': 'failed',
                        'reason': error,
                        'balance': float(current_balance)
                    })
                
                time.sleep(1)  # Small delay between transactions
            
        except Exception as e:
            log_error(f"Error processing wallet {idx}: {str(e)}")
            results.append({
                'wallet_index': idx,
                'status': 'error',
                'error': str(e)
            })
    
    return results

def main():
    log_info("Multi-Wallet Balance Distributor")
    log_info(f"Connected to Network: {w3.is_connected()}")
    
    try:
        amount_per_wallet = float(input("Enter the total amount of A0GI to be sent to all recipient wallets: "))
    except ValueError:
        log_error("Amount must be a number!")
        return
    
    private_keys = load_private_keys()
    if not private_keys:
        log_error("No private keys found in pvkey.txt")
        return
    
    recipient_wallets = load_recipient_wallets()
    if not recipient_wallets:
        return
    
    log_info(f"\nDistribution Configuration:")
    log_info(f"Number of sender wallets: {len(private_keys)}")
    log_info(f"Number of recipient wallets: {len(recipient_wallets)}")
    log_info(f"Amount per recipient: {amount_per_wallet / len(recipient_wallets):.6f} A0GI")
    log_info(f"Total amount to be sent: {amount_per_wallet:.6f} A0GI")
    
    confirm = input("Proceed? (y/n): ").lower()
    if confirm != 'y':
        log_info("Process cancelled")
        return
    
    process_wallets(private_keys, recipient_wallets, amount_per_wallet)
    log_success("\nDistribution process completed.")

if __name__ == "__main__":
    main()