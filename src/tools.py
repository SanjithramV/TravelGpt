import requests
from .config import WEATHER_API_KEY, MAPS_API_KEY

def get_weather(city):
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
    response = requests.get(url).json()
    return f"{response['location']['name']} weather: {response['current']['condition']['text']}, {response['current']['temp_c']}°C"

def get_places(city):
    # Dummy placeholder (replace with Google Places or other APIs)
    return [f"Top attraction 1 in {city}", f"Top attraction 2 in {city}", f"Top attraction 3 in {city}"]
