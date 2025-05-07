from fastapi import APIRouter
from pydantic import BaseModel
from database import database

router = APIRouter()

class WalletTransaction(BaseModel):
    ngo_id: int
    amount: float
    transaction_type: str  # "add" or "deduct"

@router.post("/wallet/transaction")
def wallet_transaction(txn: WalletTransaction):
    ...
