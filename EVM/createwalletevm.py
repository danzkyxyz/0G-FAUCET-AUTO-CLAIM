from eth_account import Account
import time  # Import time for delay

def generate_wallet():
    # Create a new account
    acct = Account.create()
    # Private key in hex format without the "0x" prefix
    private_key = acct.key.hex()[2:]
    # Wallet address (includes the "0x" prefix)
    wallet_address = acct.address
    return wallet_address, private_key

def main():
    try:
        number_of_wallets = int(input("How many wallets would you like to generate: "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    with open("wallet.txt", "w") as wallet_file, open("pvkey.txt", "w") as pvkey_file:
        for i in range(number_of_wallets):
            wallet_address, private_key = generate_wallet()
            wallet_file.write(wallet_address + "\n")
            pvkey_file.write(private_key + "\n")
            print(f"[{i+1}] Wallet Address: {wallet_address}")
            print(f"[{i+1}] Private Key: {private_key}")
            
            # Add a 1-second delay
            time.sleep(1)

if __name__ == "__main__":
    main()
