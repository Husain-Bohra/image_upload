import os
import base64
import json
import requests

# --- CONFIG ---
API_KEY = os.getenv("GROQ_API_KEY")

IMAGES_FOLDER = "images"
OUTPUT_FILE = "results.json"

# --- PROMPT ---
PROMPT = """
You are a nutrition expert. Look at this food plate image and identify every food item visible.

Return ONLY a valid JSON array like this (no extra text):
[
  {"food": "rice", "quantity_grams": 150},
  {"food": "dal", "quantity_grams": 100},
  {"food": "roti", "quantity_grams": 80}
]

Rules:
- List every food item you can see
- Estimate quantity in grams as accurately as possible
- Use simple, common food names
- Return ONLY the JSON array, nothing else
"""

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def analyze_image(image_path):
    ext = image_path.lower().split(".")[-1]
    mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"

    payload = {
        "contents": [{
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": mime, "data": encode_image(image_path)}}
            ]
        }]
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent?key={API_KEY}"
    response = requests.post(url, json=payload)
    response.raise_for_status()

    raw = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Clean up if model wraps in ```json
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    return json.loads(raw.strip())

def main():
    if not os.path.exists(IMAGES_FOLDER):
        print(f"❌ Folder '{IMAGES_FOLDER}' not found. Create it and add food images.")
        return

    supported = (".jpg", ".jpeg", ".png")
    images = [f for f in os.listdir(IMAGES_FOLDER) if f.lower().endswith(supported)]

    if not images:
        print("❌ No images found in the 'images' folder.")
        return

    all_results = {}

    for image_file in images:
        path = os.path.join(IMAGES_FOLDER, image_file)
        print(f"🔍 Analyzing: {image_file}")
        try:
            items = analyze_image(path)
            all_results[image_file] = items
            print(f"   ✅ Found {len(items)} items")
        except Exception as e:
            all_results[image_file] = {"error": str(e)}
            print(f"   ❌ Failed: {e}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n✅ Done! Results saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()
