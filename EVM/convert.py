from web3 import Web3

# Nama file input dan output
input_file = "pvkey.txt"
output_file = "wallet.txt"

def read_private_keys(filename):
    """Membaca private key dari file dan mengembalikannya sebagai list."""
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_address_from_private_key(private_key):
    """Mengonversi private key menjadi alamat wallet Ethereum."""
    account = Web3().eth.account.from_key(private_key)
    return account.address

# Membaca private key dari file
private_keys = read_private_keys(input_file)

# Mengonversi setiap private key menjadi address
addresses = [get_address_from_private_key(pk) for pk in private_keys]

# Menyimpan hasil ke file address.txt
with open(output_file, "w") as f:
    for address in addresses:
        f.write(address + "\n")

print(f"✅ Berhasil mengonversi {len(addresses)} private key ke alamat wallet.")
print(f"📂 Hasil disimpan di {output_file}")
