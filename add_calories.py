import json

# Calorie database: calories per 100g for common Indian foods
CALORIE_DB = {
    # Rice & Grains
    "rice": 130,
    "white rice": 130,
    "brown rice": 112,
    "jeera rice": 140,
    "biryani": 165,
    "pulao": 150,
    
    # Breads
    "roti": 71,
    "chapati": 71,
    "naan": 262,
    "paratha": 320,
    "puri": 250,
    "bhatura": 265,
    
    # Lentils & Dals
    "dal": 116,
    "dal tadka": 120,
    "dal makhani": 140,
    "moong dal": 105,
    "chana dal": 120,
    "toor dal": 115,
    "rajma": 127,
    "chole": 164,
    "chickpeas": 164,
    
    # Vegetables
    "sabzi": 50,
    "aloo": 77,
    "potato": 77,
    "paneer": 265,
    "palak paneer": 120,
    "mixed vegetables": 65,
    "bhindi": 33,
    "okra": 33,
    "baingan": 25,
    "brinjal": 25,
    "cauliflower": 25,
    "gobi": 25,
    "cabbage": 25,
    
    # Curries
    "curry": 120,
    "chicken curry": 135,
    "chicken": 165,
    "mutton": 294,
    "fish curry": 110,
    "egg curry": 155,
    "kadhi": 80,
    
    # Accompaniments
    "raita": 60,
    "curd": 60,
    "yogurt": 60,
    "pickle": 35,
    "achar": 35,
    "papad": 300,
    "chutney": 45,
    "salad": 25,
    
    # Snacks
    "samosa": 252,
    "pakora": 250,
    "vada": 240,
    "idli": 39,
    "dosa": 133,
    "uttapam": 94,
    
    # Sweets
    "gulab jamun": 200,
    "rasgulla": 186,
    "kheer": 120,
    "halwa": 300,
    "jalebi": 150,
}

def find_calories_per_100g(food_name):
    """
    Find calorie value for a food item.
    Returns calories per 100g, or 100 as default if not found.
    """
    food_lower = food_name.lower().strip()
    
    # Exact match
    if food_lower in CALORIE_DB:
        return CALORIE_DB[food_lower]
    
    # Partial match (e.g., "dal tadka" matches "dal")
    for key in CALORIE_DB:
        if key in food_lower or food_lower in key:
            return CALORIE_DB[key]
    
    # Default estimate for unknown foods
    print(f"   ⚠️  '{food_name}' not in database, using 100 cal/100g estimate")
    return 100

def calculate_calories(items):
    """
    Calculate calories for each food item based on grams.
    Returns updated items list with calories and total calories.
    """
    total_calories = 0
    
    for item in items:
        food = item["food"]
        grams = item["quantity_grams"]
        
        # Get calories per 100g and calculate for actual quantity
        cal_per_100g = find_calories_per_100g(food)
        item_calories = (cal_per_100g * grams) / 100
        
        item["calories"] = round(item_calories, 1)
        total_calories += item_calories
    
    return items, round(total_calories, 1)

def main():
    INPUT_FILE = "results.json"
    OUTPUT_FILE = "results_with_calories.json"
    
    # Load existing results
    try:
        with open(INPUT_FILE, "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: '{INPUT_FILE}' not found!")
        print("Run analyze_groq.py first to generate the results.")
        return
    
    print(f"\n📊 Adding calorie information to {len(results)} images\n")
    
    # Process each image
    for image_name, data in results.items():
        print(f"🍽️  Processing: {image_name}")
        
        items = data.get("items", [])
        
        if not items:
            data["total_calories"] = 0
            print(f"   ⚠️  No items found")
            continue
        
        # Calculate calories
        updated_items, total_calories = calculate_calories(items)
        
        # Update the results
        data["items"] = updated_items
        data["total_calories"] = total_calories
        
        print(f"   ✅ Total: {total_calories} calories")
        
        # Show breakdown
        for item in updated_items:
            print(f"      • {item['food']}: {item['quantity_grams']}g = {item['calories']} cal")
    
    # Save updated results
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Done! Results saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()