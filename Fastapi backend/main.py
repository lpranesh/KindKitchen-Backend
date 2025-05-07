from fastapi import FastAPI
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from database import get_db_connection, get_db_cursor
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

while True:
    try:
        conn = psycopg2.connect(
            database="kathir",
            user="postgres",
            password="12122005",
            host="localhost",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        print("Database successfully connected!")
        break
    except Exception as error:
        print("Failed connecting to the database")
        print("The error is", error)
        time.sleep(2)

__all__ = ["conn", "cursor"]


# Create tables

cursor.execute("""
CREATE TABLE IF NOT EXISTS Users (
    UserID SERIAL PRIMARY KEY,
    Name VARCHAR(255),
    Email VARCHAR(255) UNIQUE NOT NULL,
    PhoneNumber VARCHAR(15) UNIQUE,
    Role VARCHAR(50) CHECK (Role IN ('Donor', 'Restaurant', 'NGO', 'Delivery_Agent')),
    ProfilePicture VARCHAR(255),
    DateOfRegistration TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Password VARCHAR(255) NOT NULL,
    Street VARCHAR(255),
    City VARCHAR(100),
    State VARCHAR(100),
    PostalCode VARCHAR(20)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Delivery_Agents (
    DeliveryAgentID SERIAL PRIMARY KEY,
    UserID INT UNIQUE,
    Name VARCHAR(255) NOT NULL,
    PhoneNumber VARCHAR(15) UNIQUE NOT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Restaurants (
    RestaurantID SERIAL PRIMARY KEY,
    UserID INT UNIQUE,
    Name VARCHAR(255) NOT NULL,
    PhoneNumber VARCHAR(15) UNIQUE NOT NULL,
    Street VARCHAR(255) NOT NULL,
    City VARCHAR(100) NOT NULL,
    State VARCHAR(100) NOT NULL,
    PostalCode VARCHAR(20) NOT NULL,
    Rating INT,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS NGOs (
    NGOID SERIAL PRIMARY KEY,
    UserID INT UNIQUE,
    Name VARCHAR(255) NOT NULL,
    Street VARCHAR(255) NOT NULL,
    City VARCHAR(100) NOT NULL,
    State VARCHAR(100) NOT NULL,
    PostalCode VARCHAR(20) NOT NULL,
    PhoneNumber VARCHAR(15) UNIQUE NOT NULL,
    WalletBalance DECIMAL(10,2) DEFAULT 0.0,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Wallets (
    WalletID SERIAL PRIMARY KEY,
    NGOID INT NOT NULL,
    WalletBalance DECIMAL(10,2) DEFAULT 0.0,
    FOREIGN KEY (NGOID) REFERENCES NGOs(NGOID)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Payments (
    PaymentID SERIAL PRIMARY KEY,
    Amount DECIMAL(10,2) NOT NULL,
    PaymentDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PaymentMethod VARCHAR(50) NOT NULL CHECK (PaymentMethod IN ('Credit Card', 'Debit Card', 'UPI', 'Cash', 'Bank Transfer')),
    TransactionStatus VARCHAR(20) NOT NULL CHECK (TransactionStatus IN ('Success', 'Failed', 'Pending')),
    fromUserID INT NOT NULL,
    toUserID INT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Donors (
    DonorID SERIAL PRIMARY KEY,
    UserID INT UNIQUE,
    Name VARCHAR(255) NOT NULL,
    PhoneNumber VARCHAR(15) UNIQUE NOT NULL,
    Street VARCHAR(255) NOT NULL,
    City VARCHAR(100) NOT NULL,
    State VARCHAR(100) NOT NULL,
    PostalCode VARCHAR(20) NOT NULL,
    PaymentID INT UNIQUE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (PaymentID) REFERENCES Payments(PaymentID)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Food_Items (
    FoodItemID SERIAL PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Description TEXT,
    Available_Quantity INT NOT NULL,
    Priceforsingleitem DECIMAL(10,2) NOT NULL,
    Photo VARCHAR(255),
    FoodType VARCHAR(20) NOT NULL CHECK (FoodType IN ('Veg', 'Non-Veg')),
    expires DATE NOT NULL,
    IsAvailable BOOLEAN DEFAULT TRUE,
    RestaurantID INT,
    FOREIGN KEY (RestaurantID) REFERENCES Restaurants(RestaurantID)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Orders (
    OrderID SERIAL PRIMARY KEY,
    NGOID INT,
    DeliveryAgentID INT,
    RestaurantID INT NOT NULL,
    PaymentID INT,
    Quantity INT NOT NULL,
    TotalPrice DECIMAL(10,2),
    OrderStatus VARCHAR(20) DEFAULT 'Pending' CHECK (OrderStatus IN ('Pending', 'In Progress', 'Delivered', 'Cancelled')),
    FoodItemID INT NOT NULL,
    OrderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    DeliveryDate TIMESTAMP,
    FOREIGN KEY (NGOID) REFERENCES NGOs(NGOID),
    FOREIGN KEY (DeliveryAgentID) REFERENCES Delivery_Agents(DeliveryAgentID),
    FOREIGN KEY (RestaurantID) REFERENCES Restaurants(RestaurantID),
    FOREIGN KEY (PaymentID) REFERENCES Payments(PaymentID),
    FOREIGN KEY (FoodItemID) REFERENCES Food_Items(FoodItemID)
);
""")

conn.commit()

print("✅ Tables created/already existing in the database!")

from users import router as users_router
from ngo import router as ngo_router
from fooditem import router as fooditems_router
from payment import router as payment_router
from donor import router as donor_router
from order import router as order_router
from auth import router as auth_router

app = FastAPI()

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(ngo_router, prefix="/ngos", tags=["NGOs"])
app.include_router(fooditems_router, prefix="/fooditems", tags=["Food Items"])
app.include_router(payment_router, prefix="/payments", tags=["Payments"])
app.include_router(donor_router, prefix="/donors", tags=["Donors"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])
app.include_router(auth_router)

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Server is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify frontend origin here in production
    allow_credentials=True,
    allow_methods=["*"],  # Or ["POST", "OPTIONS"]
    allow_headers=["*"],
)


