import os
import json
import argparse
import logging
from M3GraphBuilder.graphlib.validator import find_node_discrepencies
from M3GraphBuilder.converters import Cpp
from M3GraphBuilder.utils import load_config_from_ini_file, setup_logging, validate_dir

M3GB_config = {}


def create_graph(args):
    """Handles the `create-graph` flow. Builds and optionally validates a graph."""
    verbose_logging = M3GB_config.get("logging").get("verbose")
    graph_name = args.name or os.path.splitext(os.path.basename(args.model))[0]

    output_folder = args.output if args.output else M3GB_config["output"]["path"]
    validate_dir(output_folder)
    output_path = os.path.join(output_folder, f"{graph_name}.lpg.json")
    try:

        with open(args.model, "r") as model_file:
            model_data = json.load(model_file)
            logging.info("Model successfully loaded. Building graph...")

            cpp_converter = Cpp(output_path, model_data, verbose_logging, None)
            cpp_converter.export()
            logging.info(
                f"Graph '{graph_name}' created successfully at '{output_path}'"
            )

        if args.validate:
            logging.info("Validating graph...")
            logging.info("[1/1] Checking for nonexistent edge sources and targets.")
            missing_node_ids = find_node_discrepencies(output_path)
            if missing_node_ids:
                logging.warning(
                    f"[1/1] Found {len(missing_node_ids)} edges referencing nonexistent nodes:"
                )
                logging.warning(missing_node_ids)
            else:
                logging.info("[1/1] All nodes in edges accounted for.")
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
    except json.JSONDecodeError:
        logging.error(
            "Failed to parse the JSON model file. Ensure it is properly formatted."
        )
    except Exception as e:
        logging.error(f"Failed to create graph: {e}")


def create_hierarchy(args):
    """Handles the `create-hierarchy` flow."""
    try:
        # Placeholder for logic to extract nodes and edges from a given graph
        graph_path = args.graph
        output_folder = args.output

        # Placeholder: Add extraction logic
        logging.info(
            f"Extracted nodes and edges from graph at '{graph_path}' into '{output_folder}'"
        )
    except Exception as e:
        logging.error(f"Failed to extract components: {e}")


def merge_graphs(args):
    """Handles the `merge-graphs` flow."""
    try:
        # Placeholder for logic to merge two graphs
        graph1, graph2 = args.graph1, args.graph2
        output_path = args.output

        # Placeholder: Add merging logic
        logging.info(f"Merged graphs '{graph1}' and '{graph2}' into '{output_path}'")
    except Exception as e:
        logging.error(f"Failed to merge graphs: {e}")


def merge_hierarchies(args):
    """Handles the `merge-hierarchies` flow."""
    try:
        # Placeholder: Add merging logic
        nodes1, edges1 = args.nodes1, args.edges1
        nodes2, edges2 = args.nodes2, args.edges2
        output_prefix = args.output

        logging.info(
            f"Merged hierarchies into '{output_prefix}_nodes.csv' and '{output_prefix}_edges.csv'"
        )
    except Exception as e:
        logging.error(f"Failed to merge hierarchies: {e}")


def main():
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
        "-o", "--output", required=True, help="Output folder for components."
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

    # Subcommand: Merge Components
    merge_components_parser = subparsers.add_parser(
        "merge-hierarchies", help="Merge two sets of nodes and edges."
    )
    merge_components_parser.add_argument(
        "-n1", "--name1", required=True, help="Name of the first nodes and edges files."
    )
    merge_components_parser.add_argument(
        "-n2",
        "--name2",
        required=True,
        help="Name of the second nodes and edges files.",
    )
    merge_components_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Name of the produced nodes and edges files.",
    )
    merge_components_parser.set_defaults(func=merge_hierarchies)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    M3GB_config = load_config_from_ini_file()
    setup_logging(M3GB_config, "M3GB.txt")
    main()
