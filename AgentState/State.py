from langchain_core.messages import AnyMessage
from typing import TypedDict, Annotated, List
import operator

class TravelState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int
    