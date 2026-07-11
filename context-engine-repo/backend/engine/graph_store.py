import networkx as nx

# Initialize the directed graph to hold the security context map in memory
graph = nx.DiGraph()

def get_graph():
    """Returns the central in-memory graph instance."""
    return graph

def clear_graph():
    """Clears the graph data when resetting the engine state."""
    graph.clear()