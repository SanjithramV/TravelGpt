from .tools import get_weather, get_places
from .utils import format_itinerary
from .agent import generate_itinerary

def main():
    city = input("Where do you want to travel? ")
    days = int(input("How many days? "))

    weather = get_weather(city)
    attractions = get_places(city)

    # AI-based plan
    ai_itinerary = generate_itinerary(city, days, weather, attractions)

    # Fallback simple itinerary
    fallback = format_itinerary(city, days, weather, attractions)

    print("\n✅ AI Travel Itinerary:\n")
    print(ai_itinerary or fallback)

if __name__ == "__main__":
    main()
