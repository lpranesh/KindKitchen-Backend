from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from main import conn, cursor
import oauth2 as oauth2

router = APIRouter()

class DonorDonation(BaseModel):
    donor_name: str
    amount: float
    date: str

@router.get("/ngodonations/{ngoid}", response_model=List[DonorDonation])
def get_donors_for_ngo(ngoid: int,get_current_user:int=Depends(oauth2.get_current_user)):
    try:
        # Step 1: Get userid of the NGO
        cursor.execute("SELECT userid FROM ngos WHERE ngoid = %s", (ngoid,))
        ngo_user = cursor.fetchone()
        if not ngo_user:
            raise HTTPException(status_code=404, detail="NGO not found")
        ngo_userid = ngo_user['userid']

        # Step 2: Find all payments where touserid = ngo's userid
        cursor.execute("""
            SELECT fromuserid, amount, paymentdate
            FROM payments
            WHERE touserid = %s AND transactionstatus = 'Success'
        """, (ngo_userid,))
        payments = cursor.fetchall()

        # Step 3: For each payment, get donor name using fromuserid
        result = []
        for p in payments:
            cursor.execute("SELECT name FROM donors WHERE userid = %s", (p['fromuserid'],))
            donor = cursor.fetchone()
            if donor:
                result.append({
                    "donor_name": donor['name'],
                    "amount": float(p['amount']),
                    "date": str(p['paymentdate'])  # unformatted, as you requested
                })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
