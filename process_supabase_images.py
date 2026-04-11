import os
import json
import base64
import requests
from groq import Groq

# ── CONFIG ──────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TABLE_NAME   = "food-table"
# ────────────────────────────────────────────────────────

CALORIE_DB = {
    "rice": 130, "white rice": 130, "brown rice": 112, "jeera rice": 140,
    "biryani": 165, "pulao": 150, "roti": 71, "chapati": 71, "naan": 262,
    "paratha": 320, "puri": 250, "bhatura": 265, "dal": 116, "dal tadka": 120,
    "dal makhani": 140, "moong dal": 105, "chana dal": 120, "toor dal": 115,
    "rajma": 127, "chole": 164, "chickpeas": 164, "sabzi": 50, "aloo": 77,
    "potato": 77, "paneer": 265, "palak paneer": 120, "mixed vegetables": 65,
    "bhindi": 33, "okra": 33, "baingan": 25, "brinjal": 25, "cauliflower": 25,
    "gobi": 25, "cabbage": 25, "curry": 120, "chicken curry": 135,
    "chicken": 165, "mutton": 294, "fish curry": 110, "egg curry": 155,
    "kadhi": 80, "raita": 60, "curd": 60, "yogurt": 60, "pickle": 35,
    "achar": 35, "papad": 300, "chutney": 45, "salad": 25, "samosa": 252,
    "pakora": 250, "vada": 240, "idli": 39, "dosa": 133, "uttapam": 94,
    "gulab jamun": 200, "rasgulla": 186, "kheer": 120, "halwa": 300, "jalebi": 150,
}
NUTRITION_DB = {
    # food: (carbs, protein, fat) per 100g
    "rice": (28, 2.7, 0.3),
    "biryani": (25, 9, 7),
    "roti": (47, 3, 0.4),
    "chapati": (47, 3, 0.4),
    "dal": (20, 9, 0.4),
    "dal tadka": (18, 8, 4),
    "dal makhani": (15, 8, 7),
    "paneer": (1.2, 18, 20),
    "palak paneer": (5, 8, 9),
    "chicken": (0, 31, 4),
    "chicken curry": (6, 18, 7),
    "chole": (27, 9, 3),
    "rajma": (22, 9, 0.5),
    "samosa": (30, 4, 14),
    "aloo": (17, 2, 0.1),
    "raita": (6, 3, 2),
    "curd": (6, 3, 2),
    "paratha": (36, 5, 12),
    "naan": (48, 9, 3),
    "idli": (8, 2, 0.1),
    "dosa": (24, 3, 4),
    "mutton": (0, 25, 20),
    "egg curry": (5, 12, 10),
    "sabzi": (8, 2, 2),
    "papad": (50, 22, 1),
    "salad": (4, 1, 0.2),
    "chutney": (8, 1, 0.5),
    "pickle": (5, 0.5, 5),
}

PROMPT = """You are a nutrition expert specializing in Indian food.
Analyze this food plate image and identify every food item visible.
For each item, estimate the quantity in grams based on standard portion sizes.
Return ONLY a raw JSON array, no markdown, no explanation:
[{"food": "rice", "quantity_grams": 200}, {"food": "dal", "quantity_grams": 150}]
If you cannot identify food items clearly, return an empty array: []"""


def get_calories(food_name):
    food_lower = food_name.lower().strip()
    if food_lower in CALORIE_DB:
        return CALORIE_DB[food_lower]
    for key in CALORIE_DB:
        if key in food_lower or food_lower in key:
            return CALORIE_DB[key]
    print(f"   ⚠️  '{food_name}' not in DB, using 100 cal/100g")
    return 100


def analyze_image_url(client, image_url):
    """Download image from URL and send to Groq"""
    try:
        img_data = requests.get(image_url, timeout=15).content
        base64_image = base64.b64encode(img_data).decode('utf-8')

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            temperature=0.3,
            max_tokens=1024
        )

        raw = response.choices[0].message.content.strip()
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                if part.strip().startswith("json"):
                    raw = part.strip()[4:]
                elif part.strip().startswith("["):
                    raw = part.strip()

        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            start, end = raw.find("["), raw.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
            return []

    except Exception as e:
        print(f"   ❌ Groq error: {e}")
        return []


def supabase_request(method, path, body=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    resp = requests.request(method, url, headers=headers, json=body, timeout=15)
    return resp



def get_nutrition(food_name, grams):
    food_lower = food_name.lower().strip()
    macros = NUTRITION_DB.get(food_lower)
    if not macros:
        for key in NUTRITION_DB:
            if key in food_lower or food_lower in key:
                macros = NUTRITION_DB[key]
                break
    if not macros:
        macros = (20, 5, 3)  # default estimate
    carbs  = round(macros[0] * grams / 100, 1)
    protein = round(macros[1] * grams / 100, 1)
    fat    = round(macros[2] * grams / 100, 1)
    return carbs, protein, fat

def main():
    print("\n🚀 Starting Supabase image processor...\n")

    groq_client = Groq(api_key=GROQ_API_KEY)

    # Fetch all pending rows
    resp = supabase_request("GET", f"{TABLE_NAME}?status=eq.pending&select=id,image_url,image_name")
    if resp.status_code != 200:
        print(f"❌ Failed to fetch rows: {resp.text}")
        return

    rows = resp.json()
    if not rows:
        print("✅ No pending images found.")
        return

    print(f"📋 Found {len(rows)} pending image(s)\n")

    for row in rows:
        row_id     = row["id"]
        image_url  = row.get("image_url") or row.get("image")
        image_name = row.get("image_name", f"id_{row_id}")

        print(f"🔍 Processing: {image_name} (id={row_id})")

        if not image_url:
            print("   ⚠️  No image URL, skipping")
            continue

        # Analyze with Groq
        items = analyze_image_url(groq_client, image_url)

        if not items:
            supabase_request("PATCH", f"{TABLE_NAME}?id=eq.{row_id}", {"status": "error"})
            print("   ⚠️  No items detected, marked as error")
            continue

        # Add calories
        total_calories = 0
        for item in items:
            cal = get_calories(item["food"])
            item["calories"] = round((cal * item["quantity_grams"]) / 100, 1)
            total_calories += item["calories"]
        total_calories = round(total_calories, 1)
        total_grams = sum(i["quantity_grams"] for i in items)

        # Update row in Supabase
        total_carbs = total_protein = total_fat = 0
        for item in items:
            c, p, f = get_nutrition(item["food"], item["quantity_grams"])
            item["carbs"] = c
            item["protein"] = p
            item["fat"] = f
            total_carbs += c
            total_protein += p
            total_fat += f

        update_payload = {
            "status": "completed",
            "items": json.dumps(items),
            "total_grams": total_grams,
            "total_calories": total_calories,
            "carbohydrates": round(total_carbs, 1),
            "proteins": round(total_protein, 1),
            "fats": round(total_fat, 1)
        }
        patch_resp = supabase_request("PATCH", f"{TABLE_NAME}?id=eq.{row_id}", update_payload)

        if patch_resp.status_code in [200, 204]:
            print(f"   ✅ {len(items)} items | {total_grams}g | {total_calories} cal")
            for item in items:
                print(f"      • {item['food']}: {item['quantity_grams']}g = {item['calories']} cal")
        else:
            print(f"   ❌ DB update failed: {patch_resp.text}")

    print("\n✅ All done!")


if __name__ == "__main__":
    main()