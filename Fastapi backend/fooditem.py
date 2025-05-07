import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor
from main import conn,cursor
import oauth2 as oauth2

router = APIRouter()

# Pydantic model
class FoodItem(BaseModel):
    name: str
    description: Optional[str] = None
    available_quantity: int
    priceforsingleitem: float
    photo: Optional[str] = None
    foodtype: str  # Veg or Non-Veg
    expires: date
    restaurantid: int

@router.post("/add", status_code=201)
def add_food_item(item: FoodItem):
    try:
        cursor.execute("""
            INSERT INTO Food_Items (
                Name, Description, Available_Quantity, Priceforsingleitem,
                Photo, FoodType, expires, RestaurantID
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            item.name, item.description, item.available_quantity,
            item.priceforsingleitem, item.photo, item.foodtype,
            item.expires, item.restaurantid
        ))
        conn.commit()
        return {"message": "Food item added successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
#get_current_user: int = Depends(oauth2.get_current_user)
@router.get("/firstpagefoodinfo")
def get_food_items_with_restaurant():
    try:
        
        cursor.execute("""
            SELECT 
                fi.Name AS FoodItemName,
                fi.Photo AS FoodImage,
                r.Name AS RestaurantName,
                r.Rating
            FROM Food_Items fi
            JOIN Restaurants r ON fi.RestaurantID = r.RestaurantID;
        """)
        items = cursor.fetchall()
        return {
            "count": len(items),
            "food_items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/secondpagefoodinfo")
def get_food_items_summary(get_current_user:int=Depends(oauth2.get_current_user)):
    try:
        cursor.execute("""
            SELECT 
                Name,
                Available_Quantity,
                Priceforsingleitem
            FROM Food_Items
            WHERE IsAvailable = TRUE;
        """)
        items = cursor.fetchall()
        return {"available_food_items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

