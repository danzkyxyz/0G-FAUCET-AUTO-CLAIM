from eth_account import Account
import time  # Import time untuk delay

def generate_wallet():
    # Buat akun baru
    acct = Account.create()
    # Private key dalam format hex tanpa awalan "0x"
    private_key = acct.key.hex()[2:]
    # Wallet address (sudah termasuk awalan "0x")
    wallet_address = acct.address
    return wallet_address, private_key

def main():
    try:
        jumlah = int(input("Berapa wallet yang diinginkan: "))
    except ValueError:
        print("Input tidak valid. Masukkan angka.")
        return

    with open("wallet.txt", "w") as wallet_file, open("pvkey.txt", "w") as pvkey_file:
        for i in range(jumlah):
            wallet_address, private_key = generate_wallet()
            wallet_file.write(wallet_address + "\n")
            pvkey_file.write(private_key + "\n")
            print(f"[{i+1}] Wallet Address: {wallet_address}")
            print(f"[{i+1}] Private Key: {private_key}")
            
            # Tambahkan delay 2 detik
            time.sleep(1)

if __name__ == "__main__":
    main()
