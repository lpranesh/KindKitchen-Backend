from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from main import conn, cursor
import oauth2 as oauth2

router = APIRouter()

class NGOOut(BaseModel):
    name: str

class NGOResponse(BaseModel):
    count: int
    ngos: List[NGOOut]

@router.get("/", response_model=NGOResponse)
#get_current_user: int = Depends(oauth2.get_current_user)
def list_all_ngos():
    try:
        cursor.execute("SELECT name FROM NGOs;")
        ngos = cursor.fetchall()
        return {
            "count": len(ngos),
            "ngos": ngos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
