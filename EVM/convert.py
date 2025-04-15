from web3 import Web3

# Input and output file names
input_file = "pvkey.txt"
output_file = "wallet.txt"

def read_private_keys(filename):
    """Reads private keys from a file and returns them as a list."""
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_address_from_private_key(private_key):
    """Converts a private key into an Ethereum wallet address."""
    account = Web3().eth.account.from_key(private_key)
    return account.address

# Read private keys from file
private_keys = read_private_keys(input_file)

# Convert each private key into an address
addresses = [get_address_from_private_key(pk) for pk in private_keys]

# Save the result to wallet.txt
with open(output_file, "w") as f:
    for address in addresses:
        f.write(address + "\n")

print(f"✅ Successfully converted {len(addresses)} private keys to wallet addresses.")
print(f"📂 The result has been saved to {output_file}")
