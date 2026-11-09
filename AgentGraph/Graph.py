from Database.PostgresConnect import PostgresConnect
from langgraph.checkpoint.postgres import PostgresSaver
from AgentState.State import TravelState
from langgraph.graph import StateGraph, START, END
from Agents.FlightAgent import FlightAgent
from Agents.HotelAgent import HotelAgent
from Agents.ItinearyAgent import ItinearyAgent
from Agents.FinalResponseAgent import FinalResponseAgent


class AgentGraph:
    def __init__(self, llm):
        self.graph = StateGraph(TravelState)
        self.flight_agent = FlightAgent(llm)
        self.hotel_agent = HotelAgent(llm)
        self.itineary_agent = ItinearyAgent(llm)
        self.response_agent = FinalResponseAgent(llm)

    def create_graph_nodes(self):
        # Fix: pass the bound *method* (a callable), not the class instance.
        # LangGraph requires a Runnable or plain callable — instances don't qualify.
        self.graph.add_node("flight_agent",   self.flight_agent.flight_agent)
        self.graph.add_node("hotel_agent",    self.hotel_agent.hotel_agent)
        self.graph.add_node("itineary_agent", self.itineary_agent.itinerary_agent)
        self.graph.add_node("final_agent",    self.response_agent.final_agent)

    def edges(self):
        self.graph.add_edge(START,            "flight_agent")
        self.graph.add_edge("flight_agent",   "hotel_agent")
        self.graph.add_edge("hotel_agent",    "itineary_agent")
        self.graph.add_edge("itineary_agent", "final_agent")
        self.graph.add_edge("final_agent",    END)

    def compile_graph(self):
        self.create_graph_nodes()
        self.edges()

        pgConn = PostgresConnect()
        conn = pgConn.connect()  # fix: no `with` block — connection must stay open

        checkpointer = PostgresSaver(conn=conn)
        checkpointer.setup()

        # Fix: compile() returns the compiled graph; assign it and return it.
        # The original did `self.graph.compile(...)` (result discarded) and then
        # `return self.graph` (the uncompiled StateGraph), so invoke() failed.
        compiled = self.graph.compile(checkpointer=checkpointer)
        return compiled
