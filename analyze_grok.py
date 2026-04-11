import os
import json
import base64
from groq import Groq

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Replace with your full key from the screenshot
IMAGES_FOLDER = "images"
OUTPUT_FILE = "results.json"

# Prompt for food analysis
PROMPT = """You are a nutrition expert specializing in Indian food.

Analyze this food plate image and identify every food item visible.
For each item, estimate the quantity in grams based on standard portion sizes.

Common Indian foods to look for: rice, dal, roti, chapati, sabzi, curry, paneer, chicken, raita, papad, pickle, salad.

Return ONLY a raw JSON array, no markdown, no explanation:
[{"food": "rice", "quantity_grams": 200}, {"food": "dal", "quantity_grams": 150}]

If you cannot identify food items clearly, return an empty array: []"""

def encode_image(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def analyze_image(client, image_path):
    """Send image to Groq vision API and get food analysis"""
    try:
        base64_image = encode_image(image_path)
        
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=1024
        )
        
        raw_response = response.choices[0].message.content
        
        # Clean up response - remove markdown code blocks if present
        raw = raw_response.strip()
        if "```" in raw:
            # Extract content between code fences
            parts = raw.split("```")
            for part in parts:
                if part.strip().startswith("json"):
                    raw = part.strip()[4:]
                elif part.strip().startswith("["):
                    raw = part.strip()
        
        # Parse JSON
        try:
            items = json.loads(raw.strip())
            return items
        except json.JSONDecodeError:
            # Try to extract JSON array manually
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
            else:
                print(f"   ⚠️  Could not parse response: {raw[:100]}...")
                return []
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return []

def main():
    # Initialize Groq client
    client = Groq(api_key=GROQ_API_KEY)
    
    # Get all image files
    if not os.path.exists(IMAGES_FOLDER):
        print(f"❌ Error: '{IMAGES_FOLDER}' folder not found!")
        return
    
    image_files = [f for f in os.listdir(IMAGES_FOLDER) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print(f"❌ No images found in '{IMAGES_FOLDER}' folder!")
        return
    
    print(f"\n🔍 Found {len(image_files)} images to analyze\n")
    
    all_results = {}
    
    for idx, image_file in enumerate(image_files, 1):
        image_path = os.path.join(IMAGES_FOLDER, image_file)
        print(f"🔍 Analyzing {idx}/{len(image_files)}: {image_file}")
        
        items = analyze_image(client, image_path)
        
        if items:
            total_grams = sum(item.get("quantity_grams", 0) for item in items)
            all_results[image_file] = {
                "items": items,
                "total_grams": total_grams
            }
            print(f"   ✅ Found {len(items)} items (Total: {total_grams}g)")
        else:
            all_results[image_file] = {
                "items": [],
                "total_grams": 0
            }
            print(f"   ⚠️  No items detected")
    
    # Save results
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Done! Results saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()