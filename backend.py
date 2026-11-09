from langchain_core.messages import HumanMessage
from AgentGraph.Graph import AgentGraph
import os
import certifi
import uuid
from Settings import settings
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_groq import ChatGroq


os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()



GOOGLE_GEMINI_API_KEY=settings.GOOGLE_GEMINI_API_KEY
if not GOOGLE_GEMINI_API_KEY:
    raise ValueError("GROQ_API_KEY missing. please add it in environment variables.")


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    api_key=GOOGLE_GEMINI_API_KEY,
    temperature=0.3,
)

def run_travel_agent(user_input: str, thread_id: str | None = None):
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    travelAgent = AgentGraph(llm)
    agentGraph = travelAgent.compile_graph()

    result = agentGraph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input
        },
        config=config
    )

    final_answer = result["messages"][-1].content

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }



    

    
    
