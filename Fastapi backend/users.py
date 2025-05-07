from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg2 import IntegrityError
from typing import Optional
from psycopg2.errors import UniqueViolation
from main import conn,cursor
import oauth2 as oauth2
from utils import hash_password
router = APIRouter()

# Common user model
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    phone_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

class Usersignup(BaseModel):
    email: str
    password: str

@router.post("/signup", status_code=201)
def signup(user: Usersignup):
    print("Received data:", user.dict())
    try:
        hashed_pw = hash_password(user.password)  # Hash the password here
        print("Hashed password:", hashed_pw)

        cursor.execute("""
            INSERT INTO Users (Email, Password)
            VALUES (%s, %s)
            RETURNING UserID;
        """, (
            user.email, hashed_pw
        ))

        user_id = cursor.fetchone()["userid"]
        conn.commit()

        print("User ID:", user_id)
        return {"message": "User signed up successfully", "UserID": user_id}

    except UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

class UserExtended(BaseModel):
    Userid :int
    name: str
    role: str  # Donor, Restaurant, NGO, Delivery_Agent
    phone_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

@router.post("/register", status_code=200)
def update_user(user: UserExtended):
    print("Received data for update:", user.dict())
    try:
        # Check if user exists
        cursor.execute("SELECT * FROM Users WHERE UserID = %s;", (user.Userid,))
        existing_user = cursor.fetchone()
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update Users table
        cursor.execute("""
            UPDATE Users
            SET Name = %s, Role = %s, PhoneNumber = %s, Street = %s, City = %s, State = %s, PostalCode = %s
            WHERE UserID = %s;
        """, (
            user.name, user.role, user.phone_number, user.street,
            user.city, user.state, user.postal_code, user.Userid
        ))

        role_lower = user.role.lower()

        if role_lower == "donor":
            cursor.execute("""
                INSERT INTO Donors (UserID, Name, PhoneNumber, Street, City, State, PostalCode)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (user.Userid, user.name, user.phone_number, user.street, user.city, user.state, user.postal_code))

        elif role_lower == "restaurant":
            cursor.execute("""
                INSERT INTO Restaurants (UserID, Name, PhoneNumber, Street, City, State, PostalCode)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (user.Userid, user.name, user.phone_number, user.street, user.city, user.state, user.postal_code))

        elif role_lower == "ngo":
            cursor.execute("""
                INSERT INTO NGOs (UserID, Name, PhoneNumber, Street, City, State, PostalCode)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (user.Userid, user.name, user.phone_number, user.street, user.city, user.state, user.postal_code))
            # Wallet info remains unchanged

        elif role_lower == "delivery_agent":
            cursor.execute("""
                INSERT INTO Delivery_Agents (UserID, Name, PhoneNumber)
                VALUES (%s, %s, %s);
            """, (user.Userid, user.name, user.phone_number))

        else:
            raise HTTPException(status_code=400, detail="Invalid role specified")
        
        conn.commit()
        return {"message": f"{user.role} processed successfully", "UserID": user.Userid}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/updateuser/{user_id}")
def update_user(user_id: int, user: UserUpdate,get_current_user:int=Depends(oauth2.get_current_user)):
    data = user.dict(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No data provided to update.")

    # Build dynamic SQL
    columns = ', '.join(f"{key} = %s" for key in data)
    values = list(data.values())
    values.append(user_id)

    update_query = f"UPDATE Users SET {columns} WHERE userid = %s"

    try:
        cursor.execute(update_query, values)
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")
        conn.commit()
    except IntegrityError as e:
        conn.rollback()
        if "email" in str(e):
            raise HTTPException(status_code=409, detail="Email already exists.")
        elif "phonenumber" in str(e).lower():
            raise HTTPException(status_code=409, detail="Phone number already exists.")
        else:
            raise HTTPException(status_code=400, detail=f"Integrity error: {e}")
    
    return {"message": f"User with ID {user_id} updated successfully."}
