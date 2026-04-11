import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("\n📋 Enter Student Data\n")

name             = input("Student Name: ").strip()
student_id       = input("Student ID / Roll No: ").strip()
marks            = float(input("Marks (%): "))
attendance       = float(input("Attendance (%): "))
extra_curricular = input("Extra Curricular Activities (e.g. cricket, debate): ").strip()

payload = {
    "student_name":     name,
    "student_id":       student_id,
    "marks":            marks,
    "attendance":       attendance,
    "extra_curricular": extra_curricular
}

resp = requests.post(
    f"{SUPABASE_URL}/rest/v1/institutional_data",
    headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    },
    json=payload
)

if resp.status_code in [200, 201]:
    print(f"\n✅ Data uploaded successfully for {name}!")
else:
    print(f"\n❌ Failed: {resp.text}")
