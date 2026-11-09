from AgentState.State import TravelState
from langchain_core.messages import SystemMessage, HumanMessage


class FinalResponseAgent:
    def __init__(self, llm):
        self.llm = llm

    def final_agent(self, state: TravelState):
        final_prompt = f"""
            Generate the final travel response for the user.

            User Request:
            {state['user_query']}

            Flights:
            {state['flight_results']}

            Hotels:
            {state['hotel_results']}

            Itinerary:
            {state['itinerary']}

            Format the final answer beautifully using these sections:

            1. Trip Summary
            2. Flight Information
            3. Hotel Suggestions
            4. Day-by-Day Itinerary
            5. Estimated Budget
            6. Final Recommendations

            Important:
            - Be clear and practical.
            - Mention that live flight API may not provide ticket prices if pricing is unavailable.
            - Keep the response useful for real travel planning.
            """

        response = self.llm.invoke([
            SystemMessage(content="You are a professional AI travel booking assistant."),
            HumanMessage(content=final_prompt)
        ])

        return {
            "messages": [response],
            "llm_calls": state.get("llm_calls", 0) + 1
        }