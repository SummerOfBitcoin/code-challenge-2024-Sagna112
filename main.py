import os
import json
import hashlib
import ecdsa
import time


class Block:
    def __init__(self, index, previous_hash):
        self.index = index
        self.previous_hash = previous_hash

# Function to validate transactions using ecdsa and sha256
def validate_transaction(transaction):
    # Extract transaction data
    txid = transaction['vin'][0]['txid']
    data = json.dumps(transaction['vin'] + transaction['vout'])

    # Extract the public key from the witness field if it exists
    public_key = None
    if 'witness' in transaction['vin'][0] and len(transaction['vin'][0]['witness']) > 1:
        public_key = transaction['vin'][0]['witness'][1]

    # Verify ECDSA signature using ecdsa
    try:
        if public_key:
            # Try decoding public key with different formats
            vk = None
            for encoding in ['uncompressed', 'compressed']:
                try:
                    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
                    break  # If successful, break the loop
                except ecdsa.keys.MalformedPointError:
                    continue  # Try the next encoding
            if not vk:
                raise ValueError("Public key format not recognized")
            
            if not vk.verify(bytes.fromhex(transaction['vin'][0]['witness'][0]), bytes.fromhex(txid) + data.encode()):
                return False
    except (ecdsa.BadSignatureError, IndexError, ValueError):
        return False

    # Calculate hash of transaction data using sha256
    calculated_txid = hashlib.sha256((txid + data).encode()).hexdigest()
    
    # Compare calculated txid with provided txid
    if txid != calculated_txid:
        return False

    # Additional validation rules can be implemented here

    return True


# Function to form a block header and calculate hash
def mine_block(version, prev_block_hash, merkle_root, timestamp, target):
    nonce = 0
    while True:
        block_header = (
            str(version) +
            prev_block_hash +
            merkle_root +
            str(timestamp) +
            str(target) +
            str(nonce)
        )
        block_hash = hashlib.sha256(block_header.encode()).hexdigest()
        if int(block_hash, 16) < target:
            return block_hash, nonce
        nonce += 1

# Read JSON file and extract transaction data
def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Function to calculate Merkle root hash
def calculate_merkle_root(transactions):
    if len(transactions) == 0:
        return hashlib.sha256(b'').hexdigest()

    if len(transactions) == 1:
        return hashlib.sha256(hashlib.sha256(json.dumps(transactions[0]).encode()).digest()).hexdigest()

    # Concatenate and hash pairs of transaction hashes iteratively until a single hash remains
    hashes = [hashlib.sha256(json.dumps(tx).encode()).digest() for tx in transactions]
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])  # Duplicate the last hash if the number of hashes is odd
        hashes = [hashlib.sha256(hashes[i] + hashes[i + 1]).digest() for i in range(0, len(hashes), 2)]
    return hashes[0].hex()

# Main function to process transactions, mine block, and write output
def process_transactions(folder_path, target_difficulty):
    valid_transactions = []
    block_transactions = []

    # Read each JSON file in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)
            transaction_data = read_json_file(file_path)

            # Validate each transaction
            if validate_transaction(transaction_data):
                valid_transactions.append(transaction_data)
    
    # Sort valid transactions based on priority or any other criteria
    sorted_transactions = sorted(valid_transactions, key=lambda x: x['priority'])

    # Construct the block header
    merkle_root = calculate_merkle_root(sorted_transactions)

    # Serialize coinbase transaction (placeholder)
    coinbase_transaction = "Serialized coinbase transaction"  # Replace with actual serialization logic

    # Include coinbase transaction in the block
    block_transactions.append(coinbase_transaction)

    # Include other valid transactions in the block
    for transaction in sorted_transactions:
        block_transactions.append(transaction['vin'][0]['txid'])  # Assuming 'txid' is the key for transaction ID
    
    # Form block header
    version = 1  # Example version number
    prev_block_hash = "0000000000000000000000000000000000000000000000000000000000000000"  # Example previous block hash
    timestamp = int(time.time())  # Current Unix timestamp

    # Mine the block
    block_hash, nonce = mine_block(version, prev_block_hash, merkle_root, timestamp, target_difficulty)

    # Write output to output.txt
    with open('output.txt', 'w') as output_file:
        output_file.write("Block Header\n")
        output_file.write("Block Hash: " + block_hash + "\n")
        output_file.write("Nonce: " + str(nonce) + "\n")
        output_file.write("Coinbase Transaction: " + coinbase_transaction + "\n")
        output_file.write("Valid Transactions:\n")
        for txid in block_transactions:
            output_file.write(txid + '\n')

    return block_hash  # Return the block hash

# Function to determine the block height
def get_block_height(blockchain):
    return len(blockchain) - 1

# Function to validate a block
def validate_block(block_hash, target_difficulty):
    # Check if the block hash is not equal to 'Block Hash'
    if block_hash == 'Block Hash':
        return False

    # Check if the block hash meets the target difficulty
    if int(block_hash, 16) >= target_difficulty:
        return False
    
    # Additional block validation rules can be implemented here

    return True

# Get the current directory
current_directory = os.path.dirname(__file__)

# Define the folder path
folder_path = os.path.join(current_directory, 'mempool')

# Define the target difficulty
target_difficulty = 0x0000ffff00000000000000000000000000000000000000000000000000000000 # New target difficulty


# Create a blockchain (list of blocks) and add the genesis block
blockchain = [Block(0, "0000000000000000000000000000000000000000000000000000000000000000")]

# Call the main function with the folder path and target difficulty
process_transactions(folder_path, target_difficulty)

block_hash = process_transactions(folder_path, target_difficulty)

# Validate the mined block
if validate_block(block_hash, target_difficulty):
    print("Block is valid.")
else:
    print("Block is invalid.")

# Determine the block height
block_height = get_block_height(blockchain)
print("Block height:", block_height)
