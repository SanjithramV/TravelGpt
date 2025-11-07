import os
import random
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai

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
# API Helper Functions
# --------------------------
def get_weather(destination):
    """Fetch current weather for a city."""
    if not OPENWEATHER_KEY:
        return None
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={destination}&appid={OPENWEATHER_KEY}&units=metric"
        res = requests.get(url)
        data = res.json()
        if data.get("cod") != 200:
            return None
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"{desc}, {temp}°C"
    except Exception as e:
        print("❌ Weather API Error:", e)
        return None

def search_places_tomtom(query, limit=3):
    """Search for places using TomTom API."""
    if not TOMTOM_KEY:
        return []
    try:
        url = f"https://api.tomtom.com/search/2/search/{query}.json"
        params = {"key": TOMTOM_KEY, "limit": limit, "countrySet": "IN"}
        res = requests.get(url, params=params)
        data = res.json()
        results = [r["poi"]["name"] for r in data.get("results", []) if "poi" in r]
        return results
    except Exception as e:
        print("❌ TomTom API Error:", e)
        return []

def generate_with_gemini(prompt):
    """Generate response using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return {"source": "gemini", "text": response.text}
    except Exception as e:
        print("❌ Gemini generation error:", e)
        return None

def generate_rule_based_itinerary(destination, days, interests):
    """Rule-based fallback itinerary using TomTom."""
    interests = interests.lower()
    activity_types = {
        "nature": "park",
        "culture": "museum",
        "food": "restaurant",
        "adventure": "hiking",
        "relax": "spa",
        "temple": "temple",
        "spiritual": "temple"
    }

    itinerary = []
    for i in range(days):
        day_items = []
        for interest in interests.split(","):
            interest = interest.strip()
            keyword = activity_types.get(interest, "tourist attraction")
            places = search_places_tomtom(keyword)
            if places:
                place = random.choice(places)
                time = random.choice(["Morning", "Afternoon", "Evening"])
                day_items.append({"time": time, "activity": f"Visit {place} ({interest})"})
        while len(day_items) < 3:
            day_items.append({
                "time": random.choice(["Morning", "Afternoon", "Evening"]),
                "activity": "Explore local cafes or markets"
            })
        itinerary.append({"day": i + 1, "items": day_items})

    return {
        "source": "rule-based",
        "meta": {"destination": destination, "days": days},
        "itinerary": itinerary
    }

# --------------------------
# Routes
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

    weather_note = get_weather(destination)

    prompt = f"""
    You are an expert travel planner. Create a {days}-day travel itinerary for {destination}.
    User interests: {interests}.
    Include cultural, natural, and food-related suggestions. Avoid repetition.
    Respond in plain text, concise and structured by day.
    """

    ai_result = generate_with_gemini(prompt)
    if ai_result:
        ai_result["meta"] = {"destination": destination, "days": days, "weather_note": weather_note}
        return jsonify({"ok": True, "generated": ai_result})

    fallback = generate_rule_based_itinerary(destination, days, interests)
    fallback["meta"]["weather_note"] = weather_note
    return jsonify({"ok": True, "generated": fallback})

# --------------------------
# Render-ready Entry Point
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
