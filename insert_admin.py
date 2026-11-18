import mysql.connector

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",      # Your MySQL password
    database="innovovault"
)

cursor = conn.cursor(dictionary=True)

# Admin details
admin_id = "bitsadmin"
password = "admin@123"

# Check if admin already exists
cursor.execute(
    "SELECT * FROM admin WHERE admin_id = %s",
    (admin_id,)
)

existing_admin = cursor.fetchone()

if existing_admin:
    print("Admin already exists!")
else:
    cursor.execute(
        "INSERT INTO admin (admin_id, password) VALUES (%s, %s)",
        (admin_id, password)
    )
    conn.commit()
    print("Admin inserted successfully!")

cursor.close()
conn.close()