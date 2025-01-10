import json


def find_node_discrepencies(lpg_path):
    # try:
    with open(lpg_path, "r") as lpg:
        # Parse the JSON data
        parsed_data = json.load(lpg)

        # Extract nodes and edges arrays
        elements = parsed_data.get("elements", {})
        nodes = elements.get("nodes", [])
        edges = elements.get("edges", [])

        # Extract 'id' values from nodes and edges
        node_ids = set(node.get("data").get("id") for node in nodes)
        edge_source_ids = set(edge.get("data").get("source") for edge in edges)
        edge_target_ids = set(edge.get("data").get("target") for edge in edges)
        node_ids_in_edges = edge_source_ids | edge_target_ids

        missing_ids = []
        # Find the difference between node_ids and edge_ids
        for nodeId in node_ids_in_edges:
            if nodeId not in node_ids:
                missing_ids.append(nodeId)

        if len(missing_ids) > 1:
            missing_ids.remove(missing_ids[0])  # Remove empty set from list.

    return missing_ids
    # except Exception as e:
        # return f"lpg_validator error: {str(e)}"
    
def remove_edges_with_missing_ids(lpg_path, output_path):
    try:
        with open(lpg_path, "r") as lpg:
            # Parse the JSON data
            parsed_data = json.load(lpg)

            # Extract the elements dictionary, nodes, and edges
            elements = parsed_data.get("elements", {})
            nodes = elements.get("nodes", [])
            edges = elements.get("edges", [])

            # Filter out edges that have missing 'id' or missing 'source' or 'target'
            edges_to_keep = [edge for edge in edges if edge.get("data", {}).get("id") is not None]
            # Update the elements dictionary with the filtered edges
            elements["edges"] = edges_to_keep

            # Create a new parsed data dictionary with the updated edges
            updated_data = {
                "elements": elements
            }

            # Write the modified data to the output file
            with open(output_path, "w") as out_file:
                json.dump(updated_data, out_file)

            return f"File has been written to {output_path} without edges with missing IDs."
    
    except Exception as e:
        return f"Error while processing the file: {str(e)}"

