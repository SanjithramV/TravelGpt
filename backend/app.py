import os
import random
import json
import asyncio
import aiohttp
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai
import pycountry

# --------------------------
# Load Environment Variables
# --------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOMTOM_KEY = os.getenv("TOMTOM_KEY")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__, static_folder="static", template_folder="templates")

# --------------------------
# Async Helper Functions
# --------------------------

async def fetch_json(session, url, params):
    """Generic async JSON fetch."""
    try:
        async with session.get(url, params=params) as resp:
            return await resp.json()
    except Exception as e:
        print(f"❌ API Fetch Error: {e}")
        return {}

async def get_weather_async(session, destination):
    """Async weather lookup."""
    if not OPENWEATHER_KEY:
        return None
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": destination, "appid": OPENWEATHER_KEY, "units": "metric"}
    data = await fetch_json(session, url, params)
    if data.get("cod") != 200:
        return None
    desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    return f"{desc}, {temp}°C"

async def geocode_destination(session, destination):
    """Get coordinates for a destination using TomTom."""
    if not TOMTOM_KEY:
        return None, None
    geo_url = f"https://api.tomtom.com/search/2/geocode/{destination}.json"
    params = {"key": TOMTOM_KEY, "limit": 1}
    data = await fetch_json(session, geo_url, params)
    if not data.get("results"):
        print(f"⚠️ Geocoding failed for: {destination}")
        return None, None
    lat = data["results"][0]["position"]["lat"]
    lon = data["results"][0]["position"]["lon"]
    print(f"📍 Geocoded {destination} → {lat}, {lon}")
    return lat, lon

async def search_places_tomtom_async(session, query, destination="France", limit=3):
    """Async TomTom POI Search."""
    if not TOMTOM_KEY:
        return []
    lat, lon = await geocode_destination(session, destination)
    if lat is None or lon is None:
        return []
    url = f"https://api.tomtom.com/search/2/poiSearch/{query}.json"
    params = {"key": TOMTOM_KEY, "lat": lat, "lon": lon, "radius": 50000, "limit": limit}
    data = await fetch_json(session, url, params)
    results = [r["poi"]["name"] for r in data.get("results", []) if "poi" in r]
    print(f"🌍 Found {len(results)} {query} near {destination}")
    return results

def generate_rule_based_itinerary(destination, days, interests, poi_data=None):
    """Fallback rule-based itinerary using POI data."""
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
                places = poi_data.get(interest, []) if poi_data else []
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
                day_items.append({"time": time, "activity": "Explore a local cafe or market"})
        itinerary.append({"day": i + 1, "items": day_items})

    return {
        "source": "rule-based",
        "meta": {"destination": destination, "days": days},
        "itinerary": itinerary
    }

async def generate_with_gemini(destination, days, interests):
    """Generate structured itinerary using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        You are an expert travel planner. Create a {days}-day itinerary for {destination}.
        User interests: {interests}.
        Return ONLY valid JSON in this format:
        {{
          "days": [
            {{
              "day": 1,
              "morning": "Visit ...",
              "afternoon": "Explore ...",
              "evening": "Enjoy ..."
            }}
          ]
        }}
        Do not include markdown, commentary, or extra text.
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        try:
            parsed = json.loads(text)
            print("✅ Gemini output parsed successfully")
            return {"source": "gemini", "structured": parsed}
        except json.JSONDecodeError:
            print("⚠️ Invalid JSON — returning raw text")
            return {"source": "gemini", "text": text}
    except Exception as e:
        print("❌ Gemini generation error:", e)
        return None

# --------------------------
# Flask Routes
# --------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/itinerary", methods=["POST"])
async def api_itinerary():
    """Async route for itinerary generation."""
    print("🛰️ /api/itinerary called")
    data = request.json or {}
    destination = data.get("destination", "Unknown")
    days = int(data.get("days", 3))
    interests = data.get("interests", "culture, food")

    async with aiohttp.ClientSession() as session:
        # Run weather + POI fetch concurrently
        weather_task = asyncio.create_task(get_weather_async(session, destination))
        poi_tasks = {i: asyncio.create_task(search_places_tomtom_async(session, i.strip(), destination, limit=4))
                     for i in interests.split(",")}
        weather_note = await weather_task
        poi_data = {k: await v for k, v in poi_tasks.items()}

    # Try Gemini first
    ai_result = await generate_with_gemini(destination, days, interests)
    if ai_result:
        ai_result["meta"] = {"destination": destination, "days": days, "weather_note": weather_note}
        return jsonify({"ok": True, "generated": ai_result})

    # Fallback if Gemini fails
    fallback = generate_rule_based_itinerary(destination, days, interests, poi_data)
    fallback["meta"]["weather_note"] = weather_note
    return jsonify({"ok": True, "generated": fallback})

# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
