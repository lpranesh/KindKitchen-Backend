from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from main import conn, cursor
import oauth2 as oauth2
import traceback
from fastapi import Body

router = APIRouter()

class OrderPayload(BaseModel):
    food_item_id: int
    quantity: int
    payment_method: str  # 'Wallet', 'UPI', etc.
    status: str          # 'Success', 'Failed', 'Pending'

@router.post("/createorder/{ngoid}", status_code=201)
def create_order(ngoid: int, order: OrderPayload):
    try:
        # 1. Fetch Food Item
        cursor.execute("SELECT * FROM Food_Items WHERE FoodItemID = %s;", (order.food_item_id,))
        food_item = cursor.fetchone()
        if not food_item:
            raise HTTPException(status_code=404, detail="❌ Food item not found")
        if not food_item["isavailable"] or food_item["available_quantity"] < order.quantity:
            raise HTTPException(status_code=400, detail="❌ Not enough quantity available")

        total_price = float(food_item["priceforsingleitem"]) * order.quantity
        restaurant_id = food_item["restaurantid"]

        # 2. Get NGO and Restaurant UserIDs
        cursor.execute("SELECT userid FROM NGOs WHERE NGOID = %s;", (ngoid,))
        ngo_user = cursor.fetchone()
        if not ngo_user:
            raise HTTPException(status_code=404, detail="❌ NGO not found")

        cursor.execute("SELECT userid FROM Restaurants WHERE RestaurantID = %s;", (restaurant_id,))
        rest_user = cursor.fetchone()
        if not rest_user:
            raise HTTPException(status_code=404, detail="❌ Restaurant not found")

        ngo_user_id = ngo_user["userid"]
        rest_user_id = rest_user["userid"]

        # 3. Wallet Check (only for Wallet payments)
        if order.payment_method == "Wallet":
            cursor.execute("SELECT walletbalance FROM Wallets WHERE NGOID = %s;", (ngoid,))
            wallet = cursor.fetchone()
            if not wallet:
                raise HTTPException(status_code=404, detail="❌ NGO wallet not found")
            if wallet["walletbalance"] < total_price:
                raise HTTPException(status_code=400, detail="❌ Insufficient NGO wallet balance")

            # Deduct balance
            cursor.execute("UPDATE Wallets SET walletbalance = walletbalance - %s WHERE NGOID = %s;", (total_price, ngoid))
            cursor.execute("SELECT walletbalance FROM Wallets WHERE NGOID = %s;", (ngoid,))
            updated_balance = cursor.fetchone()["walletbalance"]
            cursor.execute("UPDATE NGOs SET walletBalance = %s WHERE NGOID = %s;", (updated_balance, ngoid))

        # 4. Insert Payment
        cursor.execute("""
            INSERT INTO Payments (fromUserID, toUserID, Amount, PaymentMethod, TransactionStatus)
            VALUES (%s, %s, %s, %s, %s) RETURNING PaymentID;
        """, (ngo_user_id, rest_user_id, total_price, order.payment_method, order.status))
        payment_id = cursor.fetchone()["paymentid"]

        # 5. Insert Order
        cursor.execute("""
            INSERT INTO Orders (
                NGOID, DeliveryAgentID, RestaurantID, PaymentID,
                Quantity, TotalPrice, OrderStatus, FoodItemID, DeliveryDate
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """, (
            ngoid,
            None,  # delivery_agent_id is NULL
            restaurant_id,
            payment_id,
            order.quantity,
            total_price,
            "Pending",
            order.food_item_id,
            None
        ))
        order_record = cursor.fetchone()

        # 6. Update food stock
        cursor.execute("""
            UPDATE Food_Items SET available_quantity = available_quantity - %s WHERE FoodItemID = %s;
        """, (order.quantity, order.food_item_id))

        conn.commit()

        return {
            "message": "✅ Order placed successfully!",
            "order": order_record
        }

    except Exception as e:
        conn.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"🔥 Internal server error: {e}")
    
# ✅ NEW ROUTE: Get orders by restaurant
@router.get("/byrestaurant/{restaurant_id}")
def get_orders_by_restaurant(restaurant_id: int):
    try:
        cursor.execute("SELECT * FROM Orders WHERE RestaurantID = %s;", (restaurant_id,))
        orders = cursor.fetchall()
        order_count = len(orders)

        if order_count == 0:
            return {"order_count": 0, "message": "No orders found for this restaurant."}

        return {
            "order_count": order_count,
            "orders": orders
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ Internal server error: {e}")

# ✅ NEW ROUTE: Get all pending orders (for Delivery Agents)
@router.get("/pending")
def get_pending_orders():
    try:
        cursor.execute("SELECT OrderID, NGOID, RestaurantID FROM Orders WHERE OrderStatus = 'Pending';")
        pending_orders = cursor.fetchall()

        if not pending_orders:
            return {
                "count": 0,
                "message": "✅ No pending orders at the moment."
            }

        result = []

        for order in pending_orders:
            orderid = order["orderid"]
            ngoid = order["ngoid"]
            restaurantid = order["restaurantid"]

            # Get NGO address
            cursor.execute("""
                SELECT Street, City, State, PostalCode
                FROM NGOs
                WHERE NGOID = %s;
            """, (ngoid,))
            ngo = cursor.fetchone()

            # Get Restaurant address
            cursor.execute("""
                SELECT Street, City, State, PostalCode
                FROM Restaurants
                WHERE RestaurantID = %s;
            """, (restaurantid,))
            restaurant = cursor.fetchone()

            result.append({
                "orderid": orderid,
                "pickup": {
                    "street": restaurant["street"],
                    "city": restaurant["city"],
                    "state": restaurant["state"],
                    "postalcode": restaurant["postalcode"]
                },
                "drop": {
                    "street": ngo["street"],
                    "city": ngo["city"],
                    "state": ngo["state"],
                    "postalcode": ngo["postalcode"]
                }
            })

        return {
            "count": len(result),
            "pending_orders": result
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ Internal server error: {e}")

# ✅ Correct Pydantic model
class OrderAssignRequest(BaseModel):
    orderid: int
    deliverymanid: int

@router.put("/assign")
def assign_order_to_delivery_agent(request: OrderAssignRequest,get_current_user:int=Depends(oauth2.get_current_user)):
    try:
        orderid = request.orderid
        deliverymanid = request.deliverymanid
        print("Assigning order:", orderid, "to deliveryman:", deliverymanid)

        # Use a fresh cursor
        cur = conn.cursor()

        # Check if order exists
        cur.execute("SELECT OrderStatus, DeliveryAgentID FROM Orders WHERE OrderID = %s;", (orderid,))
        order = cur.fetchone()
        print("ORDER FETCHED:", order)

        if not order:
            raise HTTPException(status_code=404, detail="❌ Order not found.")
        
        status, assigned_agent = order

        print("STATUS:", status)
        print("ASSIGNED_AGENT:", assigned_agent, type(assigned_agent))

        if status != 'Pending':
            cur.execute("SELECT Name FROM Delivery_Agents WHERE DeliveryAgentID = %s;", (assigned_agent,))
            agent = cur.fetchone()
            agent_name = agent[0] if agent else "Unknown"
            return {"message": f"❌ Order already taken by another delivery agent: {agent_name}"}

        # ✅ Check if agent exists
        cur.execute("SELECT Name FROM Delivery_Agents WHERE DeliveryAgentID = %s;", (deliverymanid,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="❌ Delivery agent not found.")

        # ✅ Assign order
        cur.execute(
            "UPDATE Orders SET DeliveryAgentID = %s, OrderStatus = 'In Progress' WHERE OrderID = %s;",
            (deliverymanid, orderid)
        )
        conn.commit()
        cur.close()

        return {"message": "✅ Order successfully assigned and is now In Progress."}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ Internal server error: {e}")

@router.get("/firstpage_byrestaurant/{restaurant_id}")
def get_firstpage_orders(restaurant_id: int):
    try:
        cursor.execute("""
            SELECT o.orderid, f.photo AS foodimage, f.name AS foodname, o.quantity
            FROM orders o
            LEFT JOIN food_items f ON o.fooditemid = f.fooditemid
            WHERE o.restaurantid = %s;
        """, (restaurant_id,))
        orders = cursor.fetchall()

        if not orders:
            return {
                "count": 0,
                "message": "No orders found for this restaurant."
            }

        return {
            "count": len(orders),
            "orders": orders
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ Internal server error: {e}")

@router.get("/secondpage/{order_id}")
def get_secondpage_order_details(order_id: int):
    try:
        cursor.execute("""
            SELECT o.quantity, o.totalprice, f.photo AS foodimage, n.name AS ngoname
            FROM orders o
            LEFT JOIN food_items f ON o.fooditemid = f.fooditemid
            LEFT JOIN ngos n ON o.ngoid = n.ngoid
            WHERE o.orderid = %s;
        """, (order_id,))
        result = cursor.fetchone()

        if not result:
            return {"message": "❌ Order not found."}

        return {
            "food_image": result["foodimage"],
            "quantity": result["quantity"],
            "ngo_name": result["ngoname"],
            "total_amount": result["totalprice"]
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ Internal server error: {e}")
