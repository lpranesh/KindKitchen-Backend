from random import randrange
import time
from typing import Optional
from fastapi import FastAPI,Response,status,HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError

app=FastAPI()

while True:
    try:
        conn=psycopg2.connect(
            database="uidbms",
            user="postgres",
            password="12122005",
            host="localhost",
            cursor_factory=RealDictCursor
            )
        cursor=conn.cursor()
        print("Database successfully connected!")
        break
    except Exception as error:
        print("Failed connecting to the database")
        print("The error is",error)
        time.sleep(2)

# Create NGOs table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ngos (
        NGOID SERIAL PRIMARY KEY,
        Name VARCHAR(255) NOT NULL,
        Street VARCHAR(255) NOT NULL,
        City VARCHAR(100) NOT NULL,
        State VARCHAR(100) NOT NULL,
        PostalCode VARCHAR(20) NOT NULL,
        PhoneNumber1 VARCHAR(15) UNIQUE NOT NULL,
        PhoneNumber2 VARCHAR(15) UNIQUE,
        WalletBalance DECIMAL(10,2) DEFAULT 0.0
    );
""")

# Create Payments table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Payments (
        PaymentID SERIAL PRIMARY KEY,
        NGOID INT NOT NULL,
        Amount DECIMAL(10,2) NOT NULL,
        PaymentDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (NGOID) REFERENCES NGOs(NGOID)
    );
""")

# Create Wallets table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Wallets (
        WalletID SERIAL PRIMARY KEY,
        DonationID INT,
        Amount DECIMAL(10,2) NOT NULL,
        DonationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (DonationID) REFERENCES Payments(PaymentID)
    );
""")

conn.commit()

print("NGOs, Payments, and Wallets tables created successfully.")


from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NGO(BaseModel):
    name: str
    street: str
    city: str
    state: str
    postalcode: str
    phonenumber1: str
    phonenumber2: Optional[str] = None

class User(BaseModel):
    name: str
    street: str
    city: str
    state: str
    postalcode: str
    phonenumber1: str
    phonenumber2: Optional[str] = None


class NGOUpdate(BaseModel):
    name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postalcode: Optional[str] = None
    phonenumber1: Optional[str] = None
    phonenumber2: Optional[str] = None

class Payment(BaseModel):
    ngoid: int
    amount: float


class Wallet(BaseModel):
    wallet_id: Optional[int] = None
    donation_id: Optional[int] = None
    amount: float
    donation_date: Optional[datetime] = None

@app.get("/")
def first():
    return {"Heyy!": "This is the code for ngo,payments and wallets"}

@app.get("/testdb")
def testdb():
    cursor = conn.cursor()
    cursor.execute("SELECT current_database();")
    db_name = cursor.fetchone()["current_database"]
    cursor.close()
    return {"Connected Database": db_name}

@app.post("/addngo")
def add_ngo(ngo: NGO):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ngos (name, street, city, state, postalcode, phonenumber1, phonenumber2)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (ngo.name, ngo.street, ngo.city, ngo.state, ngo.postalcode, ngo.phonenumber1, ngo.phonenumber2))
        conn.commit()
    except IntegrityError as e:
        conn.rollback()
        cursor.close()
        # Clean error message
        if "phonenumber1" in str(e):
            raise HTTPException(status_code=409, detail="Phone number 1 already exists. Please enter a new number to register this NGO.")
        elif "phonenumber2" in str(e):
            raise HTTPException(status_code=409, detail="Phone number 2 already exists. Please enter a new number to register this NGO.")
        else:
            raise HTTPException(status_code=400, detail="Database constraint error: " + str(e))
    cursor.close()
    return {"message": "NGO added successfully!"}


@app.get("/listngo")
def listngo():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ngos")
    ngos = cursor.fetchall()
    cursor.close()

    if not ngos:
        return {"message": "Database is empty. No NGOs have been registered yet."}
    
    return {"Data": ngos}

@app.put("/editngo/{ngoid}")
def edit_ngo(ngoid: int, ngo: NGOUpdate):
    data = ngo.dict(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No data to update")

    # Dynamically build SQL
    columns = ', '.join(f"{k} = %s" for k in data)
    values = list(data.values())

    query = f"UPDATE ngos SET {columns} WHERE ngoid = %s"
    values.append(ngoid)

    with conn.cursor() as cur:
        cur.execute(query, values)
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"NGO with id {ngoid} not found")
        conn.commit()

    return {"message": "NGO updated successfully"}

@app.delete("/delngo/{ngo_id}")
def delete_ngo(ngo_id: int):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ngos WHERE ngoid = %s", (ngo_id,))
    
    if cursor.rowcount == 0:
        cursor.close()
        raise HTTPException(status_code=404, detail=f"NGO with id {ngo_id} not found.")
    
    conn.commit()
    cursor.close()
    return {"message": f"NGO with id {ngo_id} has been deleted successfully."}

@app.get("/allpayments")
def get_all_payments():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments")
    payments = cursor.fetchall()
    cursor.close()

    if not payments:
        return {"message": "No payments have been recorded yet."}

    return {"all_payments": payments}


@app.get("/allpayments/{ngoid}")
def get_payments_by_ngoid(ngoid: int):
    cursor = conn.cursor()

    # Check if NGO exists first
    cursor.execute("SELECT * FROM ngos WHERE ngoid = %s", (ngoid,))
    ngo = cursor.fetchone()
    if not ngo:
        cursor.close()
        raise HTTPException(status_code=404, detail="NGO not found")

    # Get payments for that NGO
    cursor.execute("SELECT * FROM payments WHERE ngoid = %s", (ngoid,))
    payments = cursor.fetchall()
    cursor.close()

    if not payments:
        return {"message": f"No payments found for NGO with ID {ngoid}"}

    return {"payments_for_ngoid": payments}


@app.post("/addpayment")
def payment(payment: Payment):
    cursor = conn.cursor()

    # Check if NGO exists
    cursor.execute("SELECT * FROM ngos WHERE ngoid = %s", (payment.ngoid,))
    ngo = cursor.fetchone()

    if not ngo:
        cursor.close()
        raise HTTPException(status_code=404, detail="NGO not found")

    # Insert payment
    cursor.execute("""
        INSERT INTO payments (ngoid, amount)
        VALUES (%s, %s)
        RETURNING paymentid
    """, (payment.ngoid, payment.amount))
    
    payment_id = cursor.fetchone()["paymentid"]
    conn.commit()
    cursor.close()

    return {"message": "Payment successful", "payment_id": payment_id}