# Description
0G Faucet Auto Claim is a Python-based automation script designed to streamline the process of claiming testnet tokens from the 0G (ZeroGravity) faucet. This tool is tailored for developers and testers working on the 0G Newton Testnet, enabling efficient and reliable token acquisition for multiple wallets. The script integrates with the 2Captcha service to solve hCaptcha challenges automatically, supports proxy rotation for enhanced anonymity, and includes robust error handling and retry mechanisms to ensure successful claims.

## 🚀 Key Features
- ✨Multi-Wallet Support: Processes multiple wallet addresses concurrently using configurable threads.
- ✨hCaptcha Automation: Seamlessly solves hCaptcha challenges via the 2Captcha API.
- ✨Proxy Rotation: Rotates proxies from a provided list to prevent IP-based restrictions.
- ✨Balance Checking: Verifies wallet balances on the 0G Newton Testnet after claiming.
- ✨Wallet File Rotation: Automatically switches between wallet files (e.g., wallets1.txt, wallets2.txt) for batch processing.
- ✨Detailed Logging: Provides color-coded logs for tracking progress, successes, and errors.
- ✨Configurable Parameters: Allows customization of threads, retries, delays, and more.

## 🛠️ Use Case
This script is ideal for developers who need to claim testnet tokens for testing smart contracts, dApps, or other blockchain-related projects on the 0G Newton Testnet. It eliminates manual faucet interactions, saving time and ensuring consistent token acquisition across multiple wallets.

## Requirements
- ⚙️Python 3.10
- ⚙️Required libraries: requests, web3, colorama, tzlocal
- ⚙️2Captcha API key
- ⚙️List of wallet addresses (wallets.txt)
- ⚙️Proxy list (proxies.txt)

## 📦 Installation

Clone the repository:
```bash
git clone https://github.com/yourusername/0g-faucet-auto-claim.git
cd 0g-faucet-auto-claim
```

## Configure the script:
- Add your 2Captcha API key to the CAPTCHA_API_KEY variable.
- Prepare wallets.txt with wallet addresses (one per line).
- Add proxies to proxies.txt (format: http://user:pass@host:port).
- I recommend using proxies from [DATAIMPULSE](https://dataimpulse.com/?aff=124620) for more affordable and budget-friendly prices (cost juSt $5 for 5GB proxy data).



## Usage
Run the script:
```bash
python main.py
```
or
```bash
python3 main.py
```

## The script will:

- Load wallet addresses and proxies.
- Solve hCaptcha challenges for each wallet.
- Claim tokens from the 0G faucet.
- Check and display wallet balances.
- Rotate to the next wallet file (if available) after each batch.

## Configuration
Edit the following variables in the script to customize behavior:

- THREADS: Number of concurrent wallet processes.
- MAX_RETRIES: Maximum retry attempts for failed claims.
- DELAY_BETWEEN_BATCHES: Delay between wallet batches (in seconds).
- CAPTCHA_API_KEY: Your 2Captcha API key.

## 📝 Notes

- Ensure your 2Captcha account has sufficient balance for hCaptcha solving.
- Proxies are recommended to avoid faucet rate limits.
- The script assumes a stable internet connection for Web3 and API interactions.
- Always verify wallet addresses and private keys before use to prevent loss of funds.

## Buy Me a Coffee ☕
If you find this script helpful and want to support its development, consider sending a small donation to the following EVM wallet address:
```bash
0xd111dbc26d6ad2df49e4ed06044958dff2c3feda
```
Your support is greatly appreciated and helps keep the project maintained!

## Disclaimer ⚠️
This tool is for educational and testing purposes only. Use it responsibly and in accordance with the 0G faucet's terms of service. The author is not responsible for any misuse or issues arising from the script's use.
