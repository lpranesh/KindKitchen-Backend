from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Literal
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from main import conn
import oauth2 as oauth2

router = APIRouter()

# DB connection
while True:
    try:
        conn = psycopg2.connect(
            database="kathir",
            user="postgres",
            password="12122005",
            host="localhost",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        print("✅ Payment DB connection successful!")
        break
    except Exception as e:
        print("❌ Payment DB connection failed. Retrying...")
        print("Error:", e)
        time.sleep(2)

# Shared Model
class PaymentRequest(BaseModel):
    toUserID: int
    amount: float
    payment_method: Literal["Credit Card", "Debit Card", "UPI", "Cash", "Bank Transfer", "Wallet"]
    status: Literal["Success", "Failed", "Pending"]

# Validators
def validate_user(table: str, user_id: int):
    cursor.execute(f"SELECT * FROM {table} WHERE {table[:-1]}ID = %s;", (user_id,))
    return cursor.fetchone()

# 🔁 Donor → NGO
@router.post("/donor-to-ngo/{donor_id}", status_code=status.HTTP_201_CREATED)
def donor_to_ngo_payment(donor_id: int, payment: PaymentRequest,get_current_user:int=Depends(oauth2.get_current_user)):
    ngo_id = payment.toUserID

    # Fetch Donor and NGO records
    cursor.execute("SELECT userid FROM Donors WHERE donorid = %s;", (donor_id,))
    donor_user_row = cursor.fetchone()
    if not donor_user_row:
        raise HTTPException(status_code=404, detail=f"Donor {donor_id} not found")

    cursor.execute("SELECT userid FROM NGOs WHERE ngoid = %s;", (ngo_id,))
    ngo_user_row = cursor.fetchone()
    if not ngo_user_row:
        raise HTTPException(status_code=404, detail=f"NGO {ngo_id} not found")

    donor_user_id = donor_user_row["userid"]
    ngo_user_id = ngo_user_row["userid"]

    if payment.payment_method == "Wallet":
        raise HTTPException(status_code=400, detail="❌ Donors cannot use 'Wallet' as payment method")

    try:
        # Step 1: Record the payment using userIDs
        cursor.execute("""
            INSERT INTO Payments (fromUserID, toUserID, Amount, PaymentMethod, TransactionStatus)
            VALUES (%s, %s, %s, %s, %s) RETURNING *;
        """, (donor_user_id, ngo_user_id, payment.amount, payment.payment_method, payment.status))
        payment_record = cursor.fetchone()

        # Step 2: Update NGO Wallet if payment successful
        if payment.status == "Success":
            cursor.execute("""
                UPDATE Wallets 
                SET walletbalance = walletbalance + %s
                WHERE ngoid = %s;
            """, (payment.amount, ngo_id))

            cursor.execute("SELECT walletbalance FROM Wallets WHERE ngoid = %s;", (ngo_id,))
            updated_balance = cursor.fetchone()["walletbalance"]

            cursor.execute("""
                UPDATE NGOs
                SET walletBalance = %s
                WHERE ngoid = %s;
            """, (updated_balance, ngo_id))

        conn.commit()
        return {
            "message": "✅ Donor → NGO payment recorded using userIDs",
            "data": payment_record
        }

    except Exception as e:
        conn.rollback()
        print("❌ DB error occurred:", e)  # ← Add this
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
