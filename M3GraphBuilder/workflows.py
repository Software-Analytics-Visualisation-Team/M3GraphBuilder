import os
import json
import logging

#M3GB imports
from M3GraphBuilder.converters import Cpp
from M3GraphBuilder.graphlib import Arvisaninator
from M3GraphBuilder.graphlib.validator import find_node_discrepencies
from M3GraphBuilder.graphlib.merge_hierachy import merge_nodes_and_edges
from M3GraphBuilder.utils import get_and_validate_output_folder

def create_graph(args, M3GB_config):
    """
    Handles the `create-graph` flow. Builds a graph from a model JSON file 
    and optionally validates the resulting graph.

    Args:
        args: Command-line arguments object with the following attributes:
            - name: Optional custom name for the graph.
            - model: Path to the input JSON model file (required).
            - output: Directory path for the graph output.
            - validate: Boolean to indicate whether graph validation is enabled.
        M3GB_config: Configuration dictionary containing logging and output options.
            - Expects `M3GB_config["logging"]["verbose"]` for verbose logging.

    Raises:
        FileNotFoundError: If the input model file is not found.
        JSONDecodeError: If the input JSON model is improperly formatted.
        Exception: For any other unexpected errors.
    """

    verbose_logging = M3GB_config.get("logging").get("verbose")
    graph_name = args.name or os.path.splitext(os.path.basename(args.model))[0]

    output_folder = get_and_validate_output_folder(M3GB_config, args.output, "ClassViz")
    output_path = os.path.join(output_folder, f"{graph_name}.lpg.json")
    try:
        with open(args.model, "r") as model_file:
            model_data = json.load(model_file)
            logging.info("Model successfully loaded. Building graph...")

            cpp_converter = Cpp(output_path, model_data, verbose_logging, None)
            cpp_converter.export()
            logging.info(f"Graph '{graph_name}' created successfully at '{output_path}'")

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


def create_hierarchy(args, M3GB_config):
    """
    Handles the `create-hierarchy` flow. Builds a hierarchy from a graph file 
    and extracts nodes and edges into the specified output folder.

    Args:
        args: Command-line arguments object with the following attributes:
            - graph: Path to the input graph file (required).
            - output: Directory path for the hierarchy output.
        M3GB_config: Configuration dictionary containing output options.

    Raises:
        Exception: For any unexpected errors while creating the hierarchy.
    """
    try:
        graph_path = args.graph
        output_folder = get_and_validate_output_folder(M3GB_config, args.output, "ARViSAN")

        with open(graph_path, "r") as graph_file:
            graph_data = json.load(graph_file)
            logging.info("Graph successfully loaded. Building hierachy...")

            arvisaninator = Arvisaninator(M3GB_config, graph_path, output_folder)
            arvisaninator.export()
            logging.info(f"Hierachy created successfully at '{output_folder}'")

        logging.info(
            f"Extracted nodes and edges from graph at '{graph_path}' into '{output_folder}'"
        )
    except Exception as e:
        logging.error(f"Failed to create hierarchy: {e}")


def merge_graphs(args, M3GB_config):
    """
    Handles the `merge-graphs` flow. Merges two input graphs into a single graph.

    Args:
        args: Command-line arguments object with the following attributes:
            - graph1: Path to the first graph file (required).
            - graph2: Path to the second graph file (required).
            - output: Path to save the merged graph (required).
        M3GB_config: Configuration dictionary (not used in this placeholder).

    Raises:
        Exception: For any unexpected errors during graph merging.
    """
    try:
        # Placeholder for logic to merge two graphs
        graph1, graph2 = args.graph1, args.graph2
        output_path = args.output

        # Placeholder: Add merging logic
        logging.info(f"Merged graphs '{graph1}' and '{graph2}' into '{output_path}'")
    except Exception as e:
        logging.error(f"Failed to merge graphs: {e}")


def merge_hierarchies(args, M3GB_config):
    """
    Handles the `merge-hierarchies` flow. Merges two hierarchies by combining 
    nodes and edges into a new hierarchy.

    Args:
        args: Command-line arguments object with the following attributes:
            - nodes1: Path to the nodes file of the first hierarchy (required).
            - nodes2: Path to the nodes file of the second hierarchy (required).
            - nodes3: Name for the resulting merged nodes file (required).
            - output: Directory path for the merged hierarchy output (required).
            - separate: Boolean to determine if common nodes/edges should be separated.
        M3GB_config: Configuration dictionary containing output options.

    Raises:
        Exception: For any unexpected errors during hierarchy merging.
    """
    try:
        nodes1, nodes2 = args.nodes1, args.nodes2
        edges1, edges2 = nodes1.replace("-nodes.csv", "-edges.csv"), nodes2.replace(
            "-nodes.csv", "-edges.csv"
        )

        nodes3 = args.nodes3
        output_folder = get_and_validate_output_folder(M3GB_config, args.output, "ARViSAN")
        separate = args.separate

        merge_nodes_and_edges(
            nodes1_path=nodes1,
            nodes2_path=nodes2,
            edges1_path=edges1,
            edges2_path=edges2,
            separateCommon=separate,
            nodes3_name=nodes3,
            output_folder=output_folder,
        )

        logging.info(
            f"Merged hierarchies into '{nodes3}_nodes.csv' and '{nodes3}_edges.csv'"
        )
    except Exception as e:
        logging.error(f"Failed to merge hierarchies: {e}")
