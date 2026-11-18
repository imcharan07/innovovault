import csv
from db import get_connection

conn = get_connection()
cursor = conn.cursor()

# Remove old projects before importing new ones
cursor.execute("TRUNCATE TABLE previous_projects")

with open("previous_projects.csv", "r", encoding="utf-8-sig") as file:

    reader = csv.DictReader(file)

    for row in reader:

        cursor.execute("""
            INSERT INTO previous_projects
            (title, abstract, domain, technology, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            row["title"],
            row["abstract"],
            row["domain"],
            row["technology"],
            row["status"]
        ))

conn.commit()

cursor.close()
conn.close()

print("✅ Previous projects imported successfully.")