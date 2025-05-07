from fastapi import APIRouter
from pydantic import BaseModel
from database import database  # Importing the DB connection function

router = APIRouter()

# Pydantic schema for NGO
class NGO(BaseModel):
    name: str
    street: str
    city: str
    state: str
    postalcode: str
    phonenumber1: str
    phonenumber2: str | None = None
    walletbalance: float = 0.0

@router.post("/add-ngo")
def add_ngo(ngo: NGO):
    conn = get_db_connection()  # Reuse the connection function here
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO NGOs (Name, Street, City, State, PostalCode, PhoneNumber1, PhoneNumber2, WalletBalance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (ngo.name, ngo.street, ngo.city, ngo.state, ngo.postalcode,
              ngo.phonenumber1, ngo.phonenumber2, ngo.walletbalance))
        conn.commit()
        return {"message": "NGO added successfully"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()
