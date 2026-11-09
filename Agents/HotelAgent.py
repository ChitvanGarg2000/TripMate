from AgentState.State import TravelState
from tools.tavily_tool import TavilySearchTool
from langchain_core.messages import AIMessage

class HotelAgent:
    def __init__(self, llm,):
        self.llm = llm
        self.hotel_tool = TavilySearchTool()
    
    def hotel_agent(self, state: TravelState):
        query = f"Best hotels for {state['user_query']}"
        hotel_results = self.hotel_tool.tavily_search(query)
        return {
            "hotel_results": hotel_results,
            "messages":[
                AIMessage(content="Hotel results fetched.")
            ],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }
        
        