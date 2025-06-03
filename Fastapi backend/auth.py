from fastapi import APIRouter, HTTPException, status
import schemas
import utils
import oauth2
from main import conn, cursor

router = APIRouter()

@router.post("/login", response_model=schemas.UserOut)
def login(user: schemas.Userlogin):
    cursor.execute("SELECT * FROM users WHERE Email = %s", (user.Email,))
    db_user = cursor.fetchone()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid credentials"
        )

    if not utils.verify_password(user.Password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid credentials"
        )

    access_token = oauth2.create_access_token(data={"user_id": db_user["userid"]})
    return {
            "User": {
                "Userid": db_user["userid"],
                "Role": db_user["role"],
            },
            "access_token": access_token,
            "token_type": "bearer"
        }


