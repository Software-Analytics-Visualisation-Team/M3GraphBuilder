import json

file1 = "datajhotdraw-traced.json"
file2 = "datajhotdraw-summarized.json"
ofile = "datajhotdraw-trc-sum.json"

with open(file1, "r") as file:
    json1 = json.load(file)

with open(file2, "r") as file:
    json2 = json.load(file)


def merge_json_objects(json_data1, json_data2):
    merged_json = {"elements": {"nodes": [], "edges": []}}

    # Merge 'nodes'
    nodes_map = {}
    for node in json_data1["elements"]["nodes"] + json_data2["elements"]["nodes"]:
        node_id = node["data"][id]
        if node_id not in nodes_map:
            nodes_map[node_id] = node
        else:
            node1_labels = set(nodes_map[node_id]["data"]["labels"])
            node2_labels = set(node["data"]["labels"])
            nodes_map[node_id]["data"]["labels"] = list(
                node1_labels.union(node2_labels)
            )
            nodes_map[node_id]["data"]["properties"].update(node["data"]["properties"])
    merged_json["elements"]["nodes"] = list(nodes_map.values())

    # Merge edges
    edges_map = {}
    for edge in json_data1["elements"]["edges"] + json_data2["elements"]["edges"]:
        edge_id = edge["data"][id]
        if edge_id not in edges_map:
            edges_map[edge_id] = edge
        else:
            edges_map[edge_id]["data"]["properties"].update(edge["data"]["properties"])
    merged_json["elements"]["edges"] = list(edges_map.values())

    return merged_json


# Merge JSON objects
merged_json_data = merge_json_objects(json1, json2)

# Write JSON data to output file
with open(ofile, "w") as outfile:
    json.dump(merged_json_data, outfile, indent=2)
