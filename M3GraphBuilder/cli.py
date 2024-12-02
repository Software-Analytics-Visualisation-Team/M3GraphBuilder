import argparse
from M3GraphBuilder.workflows import create_graph, create_hierarchy, merge_graphs, merge_hierarchies

def setup_parser():
    """Set up the CLI parser that parses all the arguments provided to M3GB."""
    parser = argparse.ArgumentParser(
        description="A multi-flow CLI application for building ClassViz and ARVISAN graphs from M3 models."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: Create Graph
    create_graph_parser = subparsers.add_parser(
        "create-graph", help="Create a ClassViz graph from a M3 model."
    )
    create_graph_parser.add_argument(
        "-m", "--model", required=True, help="Path to the model file."
    )
    create_graph_parser.add_argument(
        "-n", "--name", help="Name of the generated graph."
    )
    create_graph_parser.add_argument(
        "-o", "--output", help="Output folder for the graph."
    )
    create_graph_parser.add_argument(
        "-v",
        "--validate",
        action="store_true",
        help="Validate that all nodes in the edges exist.",
    )
    create_graph_parser.set_defaults(func=create_graph)

    # Subcommand: Extract Components
    extract_components_parser = subparsers.add_parser(
        "create-hierarchy",
        help="Extract layered nodes and edges from a ClassViz graph.",
    )
    extract_components_parser.add_argument(
        "-g", "--graph", required=True, help="Path to the graph file."
    )
    extract_components_parser.add_argument(
        "-o", "--output", help="Output folder for components."
    )
    extract_components_parser.set_defaults(func=create_hierarchy)

    # Subcommand: Merge Graphs
    merge_graphs_parser = subparsers.add_parser(
        "merge-graphs", help="Merge two graphs."
    )
    merge_graphs_parser.add_argument(
        "-g1", "--graph1", required=True, help="Path to the first graph."
    )
    merge_graphs_parser.add_argument(
        "-g2", "--graph2", required=True, help="Path to the second graph."
    )
    merge_graphs_parser.add_argument(
        "-o", "--output", required=True, help="Output path for the merged graph."
    )
    merge_graphs_parser.set_defaults(func=merge_graphs)

    # Subcommand: Merge Hierarchies
    merge_components_parser = subparsers.add_parser(
        "merge-hierarchies",
        help="Merge two sets of hierarchies (both nodes and edges).",
    )
    merge_components_parser.add_argument(
        "-n1",
        "--nodes1",
        required=True,
        help="Path of the first nodes files.",
    )
    merge_components_parser.add_argument(
        "-n2",
        "--nodes2",
        required=True,
        help="Path of the second nodes files.",
    )
    merge_components_parser.add_argument(
        "-n3",
        "--nodes3",
        required=True,
        help="Name of the produced nodes and edges files. For example, *nodes3 argument*-nodes.csv",
    )
    merge_components_parser.add_argument(
        "-o", "--output", help="Output path for the merged nodes and edges."
    )

    merge_components_parser.add_argument(
        "-s",
        "--separate",
        action="store_true",
        help="Separate all common nodes in both hierarchies together.",
    )
    merge_components_parser.set_defaults(func=merge_hierarchies)

    return parser