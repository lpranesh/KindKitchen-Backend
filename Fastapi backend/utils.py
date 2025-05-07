from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  

def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    
    is_verified = pwd_context.verify(plain_password, hashed_password)
    return is_verified