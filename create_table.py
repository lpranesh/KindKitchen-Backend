from database import database

conn = database()
cursor = conn.cursor()

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
cursor.close()
conn.close()

print("NGOs, Payments, and Wallets tables created successfully.")
