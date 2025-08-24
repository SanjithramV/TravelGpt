# 🌍 TravelGPT – Generative AI Travel Agent

TravelGPT is an AI-powered travel assistant built using **LangChain**, **LangGraph**, and **OpenAI API**.  
It generates **customized travel itineraries** by integrating external tools such as **Weather APIs, Maps, and Activity Databases**.

---

## ✨ Features
- 🗺️ AI-generated personalized itineraries
- 🌦️ Weather-aware travel planning
- 🎭 Activity & sightseeing suggestions
- 🔗 Tool integration (APIs for maps, weather, attractions)
- 🧠 Built with LangChain + LangGraph for orchestration
- 🔍 Debugging and tracing via LangSmith

---

## 📂 Project Structure
```
TravelGPT/
│── README.md          # Project documentation
│── requirements.txt   # Dependencies
│── .gitignore         # Ignore cache, keys, env files
│── src/
│   ├── main.py        # Entry point
│   ├── agent.py       # LangChain agent logic
│   ├── tools.py       # External tool integrations (weather, maps, activities)
│   ├── utils.py       # Helper functions
│   └── config.py      # API keys & settings
│── demo.ipynb         # Example notebook
```

---

## ⚡ Setup & Installation

### 1️⃣ Clone the repo
```bash
git clone https://github.com/<your-username>/TravelGPT.git
cd TravelGPT
```

### 2️⃣ Create virtual environment
```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate    # Windows
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set environment variables  
Create a `.env` file in the project root:
```ini
OPENAI_API_KEY=your_openai_api_key
WEATHER_API_KEY=your_weather_api_key
MAPS_API_KEY=your_maps_api_key
```

### 5️⃣ Run the agent
```bash
python src/main.py
```

---

## 🧩 Example Usage
```bash
> python src/main.py
Where do you want to travel? Paris
How many days? 3
Your itinerary is ready! 🎉
```

---

## 📦 Dependencies
- Python 3.9+
- LangChain
- LangGraph
- LangSmith
- OpenAI
- Requests

Install via:
```bash
pip install -r requirements.txt
```

---

## 📜 License
MIT License © 2025 Sanjith Ram V
