import sys
import ast
import networkx as nx
import matplotlib.pyplot as plt


class AgentVisitor(ast.NodeVisitor):
    def __init__(self):
        self.graph = nx.DiGraph()
        self.agents = set()

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call) and (
            (isinstance(node.value.func, ast.Subscript) and getattr(node.value.func.value, 'id', '') == 'Agent') or
            (getattr(node.value.func, 'id', '') == 'Agent')
        ):
            agent_name = node.targets[0].id
            self.agents.add(agent_name)
            self.graph.add_node(agent_name)

            for keyword in node.value.keywords:
                if keyword.arg == "handoffs" and isinstance(keyword.value, ast.List):
                    for elt in keyword.value.elts:
                        target_agent = None
                        if isinstance(elt, ast.Name):
                            target_agent = elt.id
                        elif isinstance(elt, ast.Call) and elt.func.id == "handoff":
                            for kw in elt.keywords:
                                if kw.arg == 'agent':
                                    target_agent = kw.value.id

                        if target_agent:
                            self.graph.add_edge(agent_name, target_agent)

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute):
                attr = call.func
                if attr.attr == 'append' and len(call.args) == 1:
                    source_agent = attr.value.value.id if isinstance(attr.value, ast.Attribute) else attr.value.id
                    target_agent = call.args[0].id if isinstance(call.args[0], ast.Name) else None

                    if source_agent in self.agents and target_agent:
                        self.graph.add_edge(source_agent, target_agent)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python agent_graph.py <source_code.py>")
        sys.exit(1)

    source_file = sys.argv[1]

    with open(source_file, "r") as file:
        source_code = file.read()

        # Analyze and reconstruct the graph
        tree = ast.parse(source_code)
        visitor = AgentVisitor()
        visitor.visit(tree)
        graph = visitor.graph

        # Visualize the graph
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(graph)
        nx.draw(graph, pos, with_labels=True, node_color='skyblue', node_size=2500, font_size=12, font_weight='bold', arrowsize=20)
        plt.title("Agent Handoff Graph")
        plt.show()
