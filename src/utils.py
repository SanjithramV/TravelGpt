def format_itinerary(city, days, weather, attractions):
    itinerary = f"🌍 Travel Itinerary for {city} ({days} days)\n"
    itinerary += f"\nWeather: {weather}\n\n"
    for d in range(1, days + 1):
        itinerary += f"Day {d}: {attractions[d % len(attractions)]}\n"
    return itinerary
