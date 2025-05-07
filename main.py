'''
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# Pydantic model for NGO
class NGO(BaseModel):
    name: str
    address: str
    city: str
    state: str
    postal_code: str
    phone_number1: str
    phone_number2: Optional[str] = None
    amount_donated: float

# Sample NGO data
ngo_db: List[NGO] = [
    NGO(
        name="Hope Foundation",
        address="123 Peace Street",
        city="Chennai",
        state="Tamil Nadu",
        postal_code="600001",
        phone_number1="9876543210",
        phone_number2="9123456780",
        amount_donated=12500.50
    ),
    NGO(
        name="Helping Hands",
        address="45 Sunrise Road",
        city="Bangalore",
        state="Karnataka",
        postal_code="560001",
        phone_number1="9988776655",
        phone_number2=None,
        amount_donated=8430.75
    ),
    NGO(
        name="Green Earth NGO",
        address="67 Eco Avenue",
        city="Hyderabad",
        state="Telangana",
        postal_code="500001",
        phone_number1="9090909090",
        phone_number2="8080808080",
        amount_donated=2300.00
    ),
    NGO(
        name="Smile Trust",
        address="12 Joy Lane",
        city="Mumbai",
        state="Maharashtra",
        postal_code="400001",
        phone_number1="7777777777",
        phone_number2=None,
        amount_donated=10500.00
    ),
    NGO(
        name="Swasthya Seva",
        address="89 Health Nagar",
        city="Pune",
        state="Maharashtra",
        postal_code="411001",
        phone_number1="6666666666",
        phone_number2="9999999999",
        amount_donated=785.25
    ),
    NGO(
        name="Vidya Daan",
        address="34 Knowledge Street",
        city="Delhi",
        state="Delhi",
        postal_code="110001",
        phone_number1="8888888888",
        phone_number2=None,
        amount_donated=5000.00
    ),
    NGO(
        name="Aasha Kiran",
        address="56 Light Street",
        city="Kochi",
        state="Kerala",
        postal_code="682001",
        phone_number1="7778889990",
        phone_number2="6665554443",
        amount_donated=9720.10
    )
]

# GET endpoint using Pydantic schema
@app.get("/ngos")
def get_ngos():
    return ngo_db
'''


from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# -------------------- MODELS --------------------
class NGO(BaseModel):
    ngo_id: int
    name: str
    address: str
    contact_info: str
    wallet_balance: float = 0.0
    ngo_type: Optional[str] = None
    registration_number: Optional[str] = None
    date_of_registration: Optional[str] = None
    verification_status: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    profile_picture: Optional[str] = None

class Wallet(BaseModel):
    wallet_id: int
    ngo_id: int
    amount: float
    donation_type: Optional[str] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    wallet_status: Optional[str] = None
    donation_date: Optional[str] = None

class Payment(BaseModel):
    payment_id: int
    ngo_id: int
    amount: float
    payment_date: str
    payment_method: str
    transaction_status: str
    reference_id: str

class NGOUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    phone_number1: Optional[str] = None
    phone_number2: Optional[str] = None
    
# -------------------- DATABASES --------------------
ngo_db: List[NGO] = []
wallet_db: List[Wallet] = []
payment_db: List[Payment] = []

# -------------------- API ENDPOINTS --------------------

@app.post("/addngo")
def add_ngo(ngo: NGO):
    ngo.wallet_balance = 0.0
    ngo_db.append(ngo)
    return {"message": "NGO added successfully", "ngo": ngo}

@app.put("/editngo/{ngo_id}")
def edit_ngo(ngo_id: int, updated_ngo: NGO):
    for idx, ngo in enumerate(ngo_db):
        if ngo.ngo_id == ngo_id:
            ngo_db[idx] = updated_ngo
            return {"message": "NGO updated successfully", "ngo": updated_ngo}
    return {"error": "NGO not found"}

@app.delete("/delngo/{ngo_id}")
def delete_ngo(ngo_id: int):
    global ngo_db
    ngo_db = [ngo for ngo in ngo_db if ngo.ngo_id != ngo_id]
    return {"message": "NGO deleted successfully"}

@app.post("/savedonation")
def save_donation(wallet: Wallet):
    wallet_db.append(wallet)
    # Update NGO wallet balance
    for ngo in ngo_db:
        if ngo.ngo_id == wallet.ngo_id:
            ngo.wallet_balance += wallet.amount
            break
    return {"message": "Donation saved successfully", "wallet": wallet}

@app.post("/updatewallet/{ngo_id}")
def update_wallet(ngo_id: int, amount: float):
    for ngo in ngo_db:
        if ngo.ngo_id == ngo_id:
            ngo.wallet_balance += amount
            return {"message": "Wallet updated successfully", "new_balance": ngo.wallet_balance}
    return {"error": "NGO not found"}

@app.post("/addpayment")
def add_payment(payment: Payment):
    payment_db.append(payment)
    return {"message": "Payment saved successfully", "payment": payment}

@app.get("/ngos")
def get_ngos():
    return ngo_db

@app.get("/wallets")
def get_wallets():
    return wallet_db

@app.get("/payments")
def get_payments():
    return payment_db
