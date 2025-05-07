from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

class UserCreate(BaseModel):
    Name : str
    Email : EmailStr
    Password : str
    role : str 
    street : str
    city : str
    state : str
    PostalCode : str
    contactNumber : str

class Userlogin(BaseModel):
    Email : EmailStr
    Password : str


class UserOut(BaseModel):
    User: dict
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None