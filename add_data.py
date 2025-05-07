import psycopg2

# ---------------- DB Connection ----------------
try:
    conn = psycopg2.connect(
        database="testdb",
        user="postgres",
        password="12122005",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    print("✅ Connected to DB")
except Exception as e:
    print(f"❌ DB connection failed: {e}")
    exit()

# ---------------- Insert Data ----------------
try:
    insert_query = """
    INSERT INTO ngos (name, street, city, state, postalcode, phonenumber1, phonenumber2, walletbalance)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    ngos_data = [
        ('Hope Foundation', '123 Peace Street', 'Chennai', 'Tamil Nadu', '600001', '9876543210', '9123456780', 12500.50),
        ('Helping Hands', '45 Sunrise Road', 'Bangalore', 'Karnataka', '560001', '9988776655', None, 8430.75),
        ('Green Earth NGO', '67 Eco Avenue', 'Hyderabad', 'Telangana', '500001', '9090909090', '8080808080', 2300.00),
        ('Smile Trust', '12 Joy Lane', 'Mumbai', 'Maharashtra', '400001', '7777777777', None, 10500.00),
        ('Swasthya Seva', '89 Health Nagar', 'Pune', 'Maharashtra', '411001', '6666666666', '9999999999', 785.25),
        ('Vidya Daan', '34 Knowledge Street', 'Delhi', 'Delhi', '110001', '8888888888', None, 5000.00),
        ('Aasha Kiran', '56 Light Street', 'Kochi', 'Kerala', '682001', '7778889990', '6665554443', 9720.10)
    ]

    for ngo in ngos_data:
        cur.execute(insert_query, ngo)

    conn.commit()
    print("✅ NGOs inserted successfully!")

except Exception as e:
    print(f"❌ Failed to insert NGOs: {e}")
    conn.rollback()

finally:
    cur.close()
    conn.close()
    print("🔒 DB connection closed.")
