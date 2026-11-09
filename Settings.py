import os
from dotenv import load_dotenv



load_dotenv()

class Settings:
    PG_URL=os.getenv("PG_URL")
    AVIATION_STACK_API_KEY=os.getenv("AVIATION_STACK_API_KEY")
    GROQ_API_KEY=os.getenv("GROQ_API_KEY")
    LANGSMITH_API_KEY=os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT=os.getenv("LANGSMITH_PROJECT")
    LANGSMITH_TRACING=os.getenv("LANGSMITH_TRACING")
    LANGSMITH_ENDPOINT=os.getenv("LANGSMITH_ENDPOINT")
    DEFAULT_ORIGIN_IATA=os.getenv("DEFAULT_ORIGIN_DATA", "IN")
    TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")
    AVIATION_STACK_BASE_URL=os.getenv("AVIATION_STACK_BASE_URL")
    GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")

settings = Settings()