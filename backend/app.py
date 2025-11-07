from flask import Flask, render_template, request, jsonify
import os, requests, json
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

# Config from environment
OPENAI_KEY = os.getenv("OPENAI_API_KEY")  # optional
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")  # optional
OWM_KEY = os.getenv("OPENWEATHER_KEY")    # optional

def geocode_place(place):
    """Geocode using TomTom API"""
    key = os.getenv("TOMTOM_KEY")
    if not key:
        return None
    url = f"https://api.tomtom.com/search/2/geocode/{requests.utils.requote_uri(place)}.json"
    params = {"key": key, "limit": 1}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        if data.get("results"):
            loc = data["results"][0]["position"]
            address = data["results"][0].get("address", {}).get("freeformAddress", place)
            return {"name": address, "lat": loc["lat"], "lng": loc["lon"]}
    except Exception as e:
        app.logger.warning("TomTom geocode failed: %s", e)
    return None


def get_weather(lat, lon):
    """Attempt to fetch current weather via OpenWeatherMap (optional). Returns simple string or None"""
    if not OWM_KEY:
        return None
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": OWM_KEY, "units": "metric"}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        d = r.json()
        desc = d["weather"][0]["description"]
        temp = d["main"]["temp"]
        return f"{desc}, {temp}°C"
    except Exception as e:
        app.logger.warning("Weather fetch failed: %s", e)
    return None

def generate_rule_based_itinerary(destination, days, interests, weather_note=None):
    """Simple offline generator that creates an itinerary using heuristics and canned activities"""
    base_activities = {
        "nature": ["City park / nature reserve", "Hiking trail", "Scenic viewpoint", "Botanical garden"],
        "culture": ["City museum", "Historic walking tour", "Art gallery", "Local market"],
        "food": ["Food walking tour", "Local restaurant tasting", "Street food stalls", "Cooking class"],
        "adventure": ["Kayaking / water sports", "Zipline / outdoor activity", "Cycling tour", "Rock climbing (guided)"],
        "relax": ["Spa / wellness center", "Beach / lake day", "Cafe hop", "Sunset viewpoint"]
    }
    # flatten fallback activities
    default = ["City highlights tour", "Local market visit", "Popular viewpoint", "Leisure time / cafe"]
    plan = []
    interests = [i.strip().lower() for i in interests.split(",") if i.strip()]
    if not interests:
        interests = ["culture","food"]
    for day in range(1, days+1):
        day_plan = {"day": day, "items": []}
        # pick interest for the day in round-robin
        interest = interests[(day-1) % len(interests)]
        candidates = base_activities.get(interest, default)
        # pick two items
        first = candidates[(day*2-2) % len(candidates)]
        second = candidates[(day*2-1) % len(candidates)]
        day_plan["items"].append({"time": "Morning", "activity": first})
        day_plan["items"].append({"time": "Afternoon", "activity": second})
        # optionally add evening suggestion
        day_plan["items"].append({"time": "Evening", "activity": "Local dining / explore nightlife"})
        plan.append(day_plan)
    meta = {"destination": destination, "days": days, "interests": interests, "weather_note": weather_note}
    return {"meta": meta, "itinerary": plan, "source": "rule-based (offline)"}



def generate_with_gemini(prompt):
    """Generate itinerary using Google Gemini API"""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-1.5-pro"
        response = model.generate_content(prompt)
        text = response.text
        return {"text": text, "source": "gemini"}
    except Exception as e:
        app.logger.warning("Gemini generation failed: %s", e)
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/itinerary", methods=["POST"])
def api_itinerary():
    data = request.json or {}
    destination = data.get("destination","Unknown")
    days = int(data.get("days", 3))
    interests = data.get("interests", "culture, food")
    # try geocode
    geodata = geocode_place(destination)
    weather_note = None
    if geodata:
        weather_note = get_weather(geodata["lat"], geodata["lng"])
    # Try OpenAI generation first if key present
    prompt = f"Create a {days}-day travel itinerary for {destination}. Interests: {interests}. Current weather: {weather_note}."
    ai_resp = generate_with_gemini(prompt)
    if ai_resp:
        return jsonify({"ok": True, "generated": ai_resp})
    # Fallback to rule-based generator
    fallback = generate_rule_based_itinerary(destination, days, interests, weather_note)
    return jsonify({"ok": True, "generated": fallback})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 7860)), debug=True)
