from langchain import OpenAI, LLMChain
from langchain.prompts import PromptTemplate
from .config import OPENAI_API_KEY

def generate_itinerary(city, days, weather, attractions):
    prompt = PromptTemplate(
        input_variables=["city", "days", "weather", "attractions"],
        template=(
            "You are a travel planner AI. Plan a {days}-day trip to {city}.\n"
            "Weather info: {weather}\n"
            "Suggested attractions: {attractions}\n"
            "Provide a detailed daily itinerary with activities."
        ),
    )
    llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.7)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(city=city, days=days, weather=weather, attractions=attractions)
