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

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__, static_folder="static", template_folder="templates")

# --------------------------
# Async Helper Functions
# --------------------------

async def fetch_json(session, url, params=None):
    try:
        async with session.get(url, params=params) as resp:
            return await resp.json()
    except Exception as e:
        print("❌ Fetch error:", e)
        return {}

async def get_weather_async(session, destination):
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
    if not TOMTOM_KEY:
        return None, None
    url = f"https://api.tomtom.com/search/2/geocode/{destination}.json"
    params = {"key": TOMTOM_KEY, "limit": 1}
    data = await fetch_json(session, url, params)
    if not data.get("results"):
        return None, None
    lat = data["results"][0]["position"]["lat"]
    lon = data["results"][0]["position"]["lon"]
    return lat, lon

async def search_places_tomtom_async(session, query, destination, limit=5):
    lat, lon = await geocode_destination(session, destination)
    if lat is None or lon is None:
        return []
    url = f"https://api.tomtom.com/search/2/poiSearch/{query}.json"
    params = {"key": TOMTOM_KEY, "lat": lat, "lon": lon, "radius": 50000, "limit": limit}
    data = await fetch_json(session, url, params)
    results = [r["poi"]["name"] for r in data.get("results", []) if "poi" in r]
    return results

async def generate_with_gemini_async(destination, days, interests):
    prompt = f"""
    You are an expert travel planner. Create a {days}-day itinerary for {destination}.
    User interests: {interests}.
    Each day should have Morning, Afternoon, and Evening activities.
    Avoid repetition. Suggest unique experiences.
    Return ONLY valid JSON in this format:
    {{
      "days": [
        {{"day": 1, "morning": "...", "afternoon": "...", "evening": "..."}}
      ]
    }}
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Run Gemini in thread to avoid blocking
        response = await asyncio.to_thread(model.generate_content, prompt)
        text = response.text.strip()
        return json.loads(text)
    except Exception as e:
        print("❌ Gemini async error:", e)
        return None

def generate_rule_based_itinerary(destination, days, interests, poi_data=None):
    interests = interests.lower()
    activity_types = {
        "nature": "park", "culture": "museum", "food": "restaurant",
        "adventure": "hiking", "relax": "spa", "temple": "temple",
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
                choices = [p for p in places if p not in used_places]
                if choices:
                    place = random.choice(choices)
                    used_places.add(place)
                    day_items.append({"time": time, "activity": f"Visit {place} ({interest})"})
                    added = True
                    break
            if not added:
                day_items.append({"time": time, "activity": "Explore a local cafe or market"})
        itinerary.append({"day": i + 1, "items": day_items})
    return {"source": "rule-based", "meta": {"destination": destination, "days": days}, "itinerary": itinerary}

# --------------------------
# Flask Routes
# --------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/itinerary", methods=["POST"])
async def api_itinerary():
    data = request.json or {}
    destination = data.get("destination", "Unknown")
    days = int(data.get("days", 3))
    interests = data.get("interests", "culture, food")

    async with aiohttp.ClientSession() as session:
        weather_task = asyncio.create_task(get_weather_async(session, destination))
        poi_tasks = {i: asyncio.create_task(search_places_tomtom_async(session, i.strip(), destination))
                     for i in interests.split(",")}
        weather_note = await weather_task
        poi_data = {k: await v for k, v in poi_tasks.items()}

    ai_result = await generate_with_gemini_async(destination, days, interests)
    if ai_result:
        return jsonify({"ok": True, "generated": {"source": "gemini", "structured": ai_result, "meta": {"destination": destination, "days": days, "weather_note": weather_note}}})

    fallback = generate_rule_based_itinerary(destination, days, interests, poi_data)
    fallback["meta"]["weather_note"] = weather_note
    return jsonify({"ok": True, "generated": fallback})

# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
