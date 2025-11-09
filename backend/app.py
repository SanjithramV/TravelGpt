import os
import random
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai
import pycountry
import traceback

# --------------------------
# Load Environment Variables
# --------------------------
load_dotenv()
print("🔍 Checking environment variable visibility in Render...")
print("🔹 GEMINI_API_KEY present:", bool(os.getenv("GEMINI_API_KEY")))
print("🔹 TOMTOM_KEY present:", bool(os.getenv("TOMTOM_KEY")))
print("🔹 OPENWEATHER_KEY present:", bool(os.getenv("OPENWEATHER_KEY")))


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOMTOM_KEY = os.getenv("TOMTOM_KEY")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️ GEMINI_API_KEY not found. Gemini generation will not work.")

app = Flask(__name__, static_folder="static", template_folder="templates")

# --------------------------
# API Helper Functions
# --------------------------

def get_country_code(destination):
    """Extract country code (ISO alpha-2) from destination."""
    try:
        country = pycountry.countries.lookup(destination.split(",")[-1].strip())
        return country.alpha_2
    except:
        return "US"  # fallback

def get_weather(destination):
    """Fetch current weather for a city."""
    if not OPENWEATHER_KEY:
        print("⚠️ OPENWEATHER_KEY missing, skipping weather fetch.")
        return None
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={destination}&appid={OPENWEATHER_KEY}&units=metric"
        res = requests.get(url)
        data = res.json()
        if data.get("cod") != 200:
            print(f"⚠️ Weather fetch failed for {destination}: {data}")
            return None
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"{desc}, {temp}°C"
    except Exception as e:
        print("❌ Weather API Error:", e)
        return None

def search_places_tomtom(query, destination="France", limit=3):
    """Search nearby places using TomTom Geocoding + POI Search."""
    if not TOMTOM_KEY:
        print("⚠️ TOMTOM_KEY missing, skipping POI search.")
        return []
    try:
        # Geocode destination
        geo_url = f"https://api.tomtom.com/search/2/geocode/{destination}.json"
        geo_params = {"key": TOMTOM_KEY, "limit": 1}
        geo_res = requests.get(geo_url, params=geo_params)
        geo_data = geo_res.json()
        if not geo_data.get("results"):
            print(f"⚠️ Geocoding failed for: {destination}")
            return []
        lat = geo_data["results"][0]["position"]["lat"]
        lon = geo_data["results"][0]["position"]["lon"]

        # Search for POIs
        search_url = f"https://api.tomtom.com/search/2/poiSearch/{query}.json"
        search_params = {"key": TOMTOM_KEY, "lat": lat, "lon": lon, "radius": 50000, "limit": limit}
        search_res = requests.get(search_url, params=search_params)
        data = search_res.json()
        results = [r["poi"]["name"] for r in data.get("results", []) if "poi" in r]
        return results
    except Exception as e:
        print("❌ TomTom API Error:", e)
        return []

def generate_with_gemini(prompt):
    """Generate itinerary using Gemini API with better debugging."""
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in environment!")
        return None

    try:
        print("🧠 Calling Gemini API...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        # Log raw response for visibility
        print("✅ Gemini API called successfully.")
        print("🧾 Gemini Response Preview:")
        print(response.text[:500])  # limit to first 500 chars
        return {"source": "gemini", "text": response.text}

    except Exception as e:
        print("❌ Gemini generation error:")
        traceback.print_exc()
        return None

def generate_rule_based_itinerary(destination, days, interests):
    """Generate non-repetitive itinerary using TomTom results."""
    interests = interests.lower()
    activity_types = {
        "nature": "park",
        "culture": "museum",
        "food": "restaurant",
        "adventure": "hiking",
        "relax": "spa",
        "temple": "temple",
        "spiritual": "church"
    }
    itinerary = []
    used_places = set()
    for i in range(days):
        day_items = []
        for time in ["Morning", "Afternoon", "Evening"]:
            added = False
            for interest in interests.split(","):
                interest = interest.strip()
                keyword = activity_types.get(interest, "tourist attraction")
                places = search_places_tomtom(keyword, destination, limit=5)
                if places:
                    choices = [p for p in places if p not in used_places]
                    if not choices:
                        continue
                    place = random.choice(choices)
                    used_places.add(place)
                    day_items.append({"time": time, "activity": f"Visit {place} ({interest})"})
                    added = True
                    break
            if not added:
                day_items.append({"time": time, "activity": "Explore a local market or cafe"})
        itinerary.append({"day": i + 1, "items": day_items})
    return {"source": "rule-based", "meta": {"destination": destination, "days": days}, "itinerary": itinerary}

# --------------------------
# Flask Routes
# --------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/itinerary", methods=["POST"])
def api_itinerary():
    print("🛰️ /api/itinerary called")
    data = request.json or {}
    destination = data.get("destination", "Unknown")
    days = int(data.get("days", 3))
    interests = data.get("interests", "culture, food")

    print(f"📍 Destination: {destination}, Days: {days}, Interests: {interests}")

    # Get weather
    weather_note = get_weather(destination)
    print(f"🌤️ Weather info: {weather_note}")

    # Gemini Prompt
    prompt = f"""
    You are an expert travel planner. Create a {days}-day itinerary for {destination}.
    User interests: {interests}.
    Suggest unique experiences and avoid repetition.
    Each day should have Morning, Afternoon, and Evening activities.
    Respond in clear structured text.
    """

    ai_result = generate_with_gemini(prompt)

    if ai_result:
        print("🧠 Itinerary generated by Gemini")
        ai_result["meta"] = {"destination": destination, "days": days, "weather_note": weather_note}
        return jsonify({"ok": True, "generated": ai_result})

    print("⚙️ Falling back to rule-based itinerary generation...")
    fallback = generate_rule_based_itinerary(destination, days, interests)
    fallback["meta"]["weather_note"] = weather_note
    return jsonify({"ok": True, "generated": fallback})

# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 TravelGPT backend running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
