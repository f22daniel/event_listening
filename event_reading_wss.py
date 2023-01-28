import json
from web3 import Web3
from websockets import connect
import asyncio

# add your blockchain connection information
infura_url = 'https://goerli.infura.io/v3/815e996eff9c4caa8cfe1349781148b6'
w3 = Web3(Web3.HTTPProvider(infura_url))

contract_address = Web3.to_checksum_address("0x5b6c5f2032C2483251C36DA4EAd2EEe9504694dd")
contract_abi = '[{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"message","type":"string"},' \
               '{"indexed":true,"internalType":"uint256","name":"date","type":"uint256"},{"indexed":true,"internalType":"address","name":"from","type":"address"},' \
               '{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"},' \
               '{"indexed":false,"internalType":"uint256","name":"transaction","type":"uint256"}],"name":"NewTrade","type":"event"},' \
               '{"inputs":[{"internalType":"string","name":"_message","type":"string"},{"internalType":"address","name":"to","type":"address"},' \
               '{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Trade","outputs":[],"stateMutability":"payable","type":"function"}]'

contract = w3.eth.contract(address=contract_address, abi=contract_abi)
message_event = contract.events.NewTrade()
block_filter = w3.eth.filter({'fromBlock': 'latest', 'address': contract_address})

def handle_events(event):
    receipt = w3.eth.wait_for_transaction_receipt(event['transactionHash'])
    result = message_event.process_receipt(receipt)
    print(result[0]['args'])

def log_loop(event_filter):
    entries = event_filter.get_new_entries()
    # When message is successfully received and log_loop method is triggered, "event_filter.get_new_entries()" does not catch the message
    # successfully on first attempt and remains empty and skips the for loop. This is why there is the infinite loop bellow, which repeats
    # the "event_filter.get_new_entries()" until it catches the message so that it can proceed and decode the transaction receipt and
    # get the events
    while True:
        if len(entries) == 0:
            entries = event_filter.get_new_entries()
            print(f"Length is Zero!!")
            continue
        else:
            print("Passed")
            break
    print(f"event_filter_length: {entries}")
    for event in entries:
        handle_events(event)
        print(f"event_filter: {event_filter}, event: {event}")
        print("")

# Main function that is run asynchronously and independently of the rest of the program
async def get_event():
    # Initiates the connection between your dapp and the network
    async with connect("wss://goerli.infura.io/ws/v3/815e996eff9c4caa8cfe1349781148b6") as ws:
        await ws.send(json.dumps({"id": 1, "method": "eth_subscribe", "params": ["logs", {"address": [f'{contract_address}']}]}))
        # Wait for the subscription completion.
        subscription_response = await ws.recv()
        print(f"Subscription response: {subscription_response}")
        while True:
            try:
                # Wait for the message in websockets and print the contents.
                await asyncio.wait_for(ws.recv(), timeout=60)
                log_loop(block_filter)
            except asyncio.exceptions.TimeoutError:
                pass

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(get_event())
