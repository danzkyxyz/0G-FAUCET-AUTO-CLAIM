from web3 import Web3

# Konfigurasi RPC
RPC_URL = "https://0g-evm-rpc.murphynode.net"
CHAIN_ID = 16600
SYMBOL = "A0GI"

# Koneksi ke jaringan
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("Gagal terhubung ke jaringan 0G-Newton-Testnet")
    exit()

def cek_saldo(alamat):
    try:
        alamat = Web3.to_checksum_address(alamat)
        saldo = web3.eth.get_balance(alamat)
        saldo_a0gi = web3.from_wei(saldo, 'ether')
        print(f"{alamat} - Saldo {SYMBOL}: {saldo_a0gi} {SYMBOL}")
        return saldo_a0gi
    except Exception as e:
        print(f"Error pada {alamat}: {e}")
        return 0

# Baca file wallets.txt dan cek saldo untuk setiap alamat
try:
    with open("wallets.txt", "r") as file:
        wallets = [line.strip() for line in file if line.strip()]
    
    total_saldo = 0
    for wallet in wallets:
        total_saldo += cek_saldo(wallet)
    
    print(f"Total saldo semua wallet: {total_saldo} {SYMBOL}")
except FileNotFoundError:
    print("File wallets.txt tidak ditemukan.")