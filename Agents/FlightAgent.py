from AgentState.State import TravelState
from tools.flight_tool import FlightTool
from langchain_core.messages import AIMessage

class FlightAgent:
    def __init__(self, llm,):
        self.llm = llm
        self.flight_tool = FlightTool()
    
    def flight_agent(self, state: TravelState):
        query = state['user_query']
        flight_data = self.flight_tool.search_flights(query=query)
        return {
            "flight_results": flight_data,
            "messages":[
                AIMessage(content="Flight results fetched.")
            ],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

        