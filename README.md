# TravelGPT – Itinerary Planner (Prototype)

This is a compact, ready-to-run prototype of an **LLM-powered itinerary planner** with optional integrations:
- Mapbox (geocoding)
- OpenWeatherMap (current weather)
- OpenAI (LLM-based itinerary generation)

If API keys are not available, the app falls back to a rule-based offline itinerary generator so the app still works end-to-end.

## Contents
- `backend/` – Flask app serving the UI and API.
- `backend/templates/index.html` – Simple responsive UI (Bootstrap).
- `backend/static/script.js` – Client JS to call the backend API.

## How to run (locally)
1. Copy `.env.example` to `.env` inside `backend/` and add keys if available:
   ```
   cp backend/.env.example backend/.env
   # edit backend/.env and add keys like OPENAI_API_KEY, MAPBOX_TOKEN, OPENWEATHER_KEY
   ```

2. Create a virtual environment, install deps, and run:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   export FLASK_APP=app.py
   flask run --host=0.0.0.0 --port=7860
   ```
   Or simply: `python app.py` for debug mode (port 7860 by default).

3. Open http://localhost:7860 in your browser. Enter a destination, days, and interests and press **Generate Itinerary**.

## Notes for interview/demo
- If you add `OPENAI_API_KEY` in `.env`, the backend will attempt to call OpenAI ChatCompletions. If not provided, the prototype still returns a coherent rule-based plan.
- Mapbox/OpenWeather add richer geolocation and weather-aware suggestions.
- This is intentionally compact and well-commented for interview walkthroughs. You can extend it by:
  - Adding activity APIs (e.g., Google Places, Yelp) for live recommendations.
  - Integrating a vector DB + LangChain for retrieval-based itineraries/personalization.
  - Adding authentication and user profiles.

---
Good luck with your ZS Generative AI interview — feel free to ask for improvements: converting this into a React frontend, or adding OpenAI function-calling examples or LangChain integration.
