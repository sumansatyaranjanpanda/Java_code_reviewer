# graph.py
from langgraph.graph import StateGraph, START, END
from core.schema import Response
from core.node import (
    guide1_node, guide2_node, guide3_node, guide4_node, guide5_node,
    guide6_node, guide7_node, guide8_node, guide9_node, guide10_node,
    llm_node, final_updated_node
)

graph = StateGraph(Response)

# add nodes
graph.add_node("guide1_node", guide1_node)
graph.add_node("guide2_node", guide2_node)
graph.add_node("guide3_node", guide3_node)
graph.add_node("guide4_node", guide4_node)
graph.add_node("guide5_node", guide5_node)
graph.add_node("guide6_node", guide6_node)
graph.add_node("guide7_node", guide7_node)
graph.add_node("guide8_node", guide8_node)
graph.add_node("guide9_node", guide9_node)
graph.add_node("guide10_node", guide10_node)
graph.add_node("llm_node", llm_node)
graph.add_node("final_updated_node", final_updated_node)

# parallel fan-out
for i in range(1, 11):
    graph.add_edge(START, f"guide{i}_node")
    graph.add_edge(f"guide{i}_node", "llm_node")

graph.add_edge("llm_node", "final_updated_node")
graph.add_edge("final_updated_node", END)

# compile workflow
workflow = graph.compile()
