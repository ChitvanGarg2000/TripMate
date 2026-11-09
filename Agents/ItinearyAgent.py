from AgentState.State import TravelState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

class ItinearyAgent:
    def __init__(self, llm):
        self.llm = llm
    
    def itinerary_agent(self, state: TravelState):
        prompt = f"""
                Create a complete travel itinerary.

                User Query:
                {state['user_query']}

                Flight Results:
                {state['flight_results']}

                Hotel Results:
                {state['hotel_results']}

                Make the itinerary practical, budget-aware, and easy to follow.
                """

        response = self.llm.invoke([
            SystemMessage(content="You are an expert travel planner."),
            HumanMessage(content=prompt)
        ])

        return {
            "itinerary": response.content,
            "messages": [response],
            "llm_calls": state.get("llm_calls", 0) + 1
        }
