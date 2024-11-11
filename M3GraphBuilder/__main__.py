import os
import json
import argparse
from M3GraphBuilder.graph.validator import find_node_discrpenecies
from M3GraphBuilder.converters import Cpp


def get_model_file_name(file_path):
    if not os.path.exists(file_path):
        raise ValueError("Invalid file path. File does not exist.")

    base_name = os.path.basename(file_path)

    if ".json" not in base_name:
        raise ValueError("--model_path does not lead to a file with a JSON extension.")

    json_name = os.path.splitext(base_name)[0]

    return json_name


def create_graph_path(folder_path, graph_name, is_model_folder):
    if is_model_folder:
        path_list = folder_path.split("\\")
        folder_path = "\\".join(path_list[:-1])

    graph_path = f"{folder_path}\\{graph_name}.lpg.json"
    return graph_path


def main():
    parser = argparse.ArgumentParser(
        description="A CLI application for extracting a graph out of C3 model."
    )
    parser.add_argument(
        "-m_path",
        "--model_path",
        type=str,
        required=True,
        help="the path of the C3 model (Required)",
    )
    parser.add_argument(
        "-g_name",
        "--graph_name",
        type=str,
        required=False,
        help="the name of the generated graph (Optional)",
    )
    parser.add_argument(
        "-f_path",
        "--folder_path",
        type=str,
        required=False,
        help="the path to the folder in which to save the graph (Optional)",
    )
    parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="Extracts nodes describing variables, primitives and function parameters.",
    )
    parser.add_argument(
        "-v",
        "--validate",
        action="store_true",
        help="Validates whether the nodes in the generated graph, and the ones in the edges are consistent.",
    )
    args = parser.parse_args()

    if args.model_path:
        model_path = args.model_path

        if args.graph_name:
            graph_name = args.graph_name
        else:
            graph_name = get_model_file_name(model_path)

        if args.folder_path:
            graph_path = create_graph_path(args.folder_path, graph_name, False)
        else:
            graph_path = create_graph_path(model_path, graph_name, True)

        with open(model_path, "r") as model_json:
            parsed_json = json.load(model_json)

            print(f"Model successfully loaded. Building graph:")

            converter = Cpp
            cpp_converter = converter(graph_path, parsed_json, True, None)

            cpp_converter.export()
            print(f"[DONE] Graph {graph_name} successfully built in {graph_path}")

            if args.validate is True:
                print("Validating graph:")
                print("[1/1] Checking for nonexistent edge sources and targets.")
                missing_node_ids = find_node_discrpenecies(graph_path)
                if len(missing_node_ids) > 0:
                    print(
                        f"[1/1] Found {len(missing_node_ids)} edges from/to nonexistent nodes with the following IDs:"
                    )
                    print(missing_node_ids)
                else:
                    print("[1/1] All nodes in edges accounted for.")
    else:
        print("Error: Missing value: --model_path")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"Error: {str(e)}")
