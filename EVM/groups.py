def split_wallets(input_file='wallet.txt', chunk_size=50):
    with open(input_file, 'r') as f:
        wallets = [line.strip() for line in f if line.strip()]

    total_wallets = len(wallets)
    num_files = (total_wallets + chunk_size - 1) // chunk_size  # Round up

    for i in range(num_files):
        start = i * chunk_size
        end = start + chunk_size
        chunk = wallets[start:end]

        output_file = f'wallets{i+1}.txt'
        with open(output_file, 'w') as f_out:
            for address in chunk:
                f_out.write(address + '\n')

    print(f"Finished splitting {total_wallets} wallets into {num_files} files.")

if __name__ == "__main__":
    split_wallets()
