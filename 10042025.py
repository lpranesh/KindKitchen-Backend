from random import randrange
import time
from typing import Optional
from fastapi import FastAPI, Response, status, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError

app = FastAPI()

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

# Create tables

cursor.execute("""
CREATE TABLE IF NOT EXISTS Users (
    UserID SERIAL PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Email VARCHAR(255) UNIQUE NOT NULL,
    PhoneNumber VARCHAR(15) UNIQUE,
    Role VARCHAR(50) NOT NULL CHECK (Role IN ('Donor', 'Restaurant', 'NGO', 'Delivery_Agent')),
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
    PaymentID INT UNIQUE,
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

print("Tables created/already existing in the database!")