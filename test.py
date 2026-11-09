from tools.tavily_tool import TavilySearchTool
from backend import run_travel_agent

# search_tool = TavilySearchTool()

# response = process_query("what is the distance from delhi to munsiyari ?")

# user_input = input("Enter travel request: ")

response = run_travel_agent(
    user_input="Prepare itineary for munsiyari",
    thread_id="test_user"
)

print("\nFINAL RESPONSE:\n")
print(response["answer"])