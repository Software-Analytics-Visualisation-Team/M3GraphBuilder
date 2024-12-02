import pandas as pd
from M3GraphBuilder.graphlib.graph import create_node, create_edge

global_namespace_const = "global-namespace"


def handle_common_node_parent(common_node_id, edges1, edges2, new_parent_id):
    """
    Removes the CONTAINS edge from edges2, and updates it in edges1 to a new parent. To be used to separate common nodes.

    Args:
        common_node (str): The `id` to check for in the `:END_ID` column.
        edges1 (pd.DataFrame): First dataframe containing edge data.
        edges2 (pd.DataFrame): Second dataframe containing edge data.
        new_parent_id(str): The `id` of the node that will contain the `common_node`

    Returns:
        edges1, edges2: Both dataframes, updated.
    """

    def delete_edge_by_target(df, edge_type, edge_target):

        filtered_df = df[~((df[":TYPE"] == edge_type) & (df[":END_ID"] == edge_target))]

        return filtered_df

    edges2 = delete_edge_by_target(edges2, "CONTAINS", common_node_id)

    condition = (edges1[":TYPE"] == "CONTAINS") & (edges1[":END_ID"] == common_node_id)

    edges1.loc[condition, [":START_ID", "id"]] = [new_parent_id, f"{new_parent_id}-contains-{common_node_id}"]

    return edges1, edges2


def compare_for_same_parent(id, edges1, edges2):
    """
    Checks whether the `:START_ID` values match for a given `id` in two dataframes (`edges1` and `edges2`),
    based on specific conditions.

    Args:
        id (str or int): The `id` to check for in the `:END_ID` column.
        edges1 (pd.DataFrame): First dataframe containing edge data.
        edges2 (pd.DataFrame): Second dataframe containing edge data.

    Returns:
        bool: True if the `:START_ID` values match for the valid rows in both dataframes,
              or if one of the values matches `global_namespace_const`. False otherwise.

    Raises:
        ValueError: If more than one row matches the criteria in either dataframe.
    """
    # Filter rows based on criteria
    containment_edge1 = edges1[
        (edges1[":END_ID"] == id) & (edges1[":TYPE"] == "CONTAINS")
    ]
    containment_edge2 = edges2[
        (edges2[":END_ID"] == id) & (edges2[":TYPE"] == "CONTAINS")
    ]

    # Ensure at most one matching row exists in each dataframe
    if len(containment_edge1) > 1 or len(containment_edge2) > 1:
        print(containment_edge1[[":START_ID", ":END_ID"]])
        print(containment_edge2[[":START_ID", ":END_ID"]])
        raise ValueError(
            "Each list of edges should contain at most one CONTAINS edge matching the criteria."
        )

    # Extract `:START_ID` values

    parent_node_id_1 = containment_edge1.iloc[0][":START_ID"]
    parent_node_id_2 = containment_edge2.iloc[0][":START_ID"]

    # Compare `:START_ID` values or check for global_namespace_const
    same_parent = parent_node_id_1 == parent_node_id_2
    in_global_namespace = global_namespace_const in parent_node_id_1 and global_namespace_const in parent_node_id_2
    return  same_parent, in_global_namespace


def handle_common_application_node(nodes1, nodes2, edges1):
    common_application_node_id = "Common"
    common_application_node_label = "Application"
    common_node_exists = (
        (nodes1["id:ID"] == common_application_node_id)
        & (nodes1[":LABEL"] == common_application_node_label)
    ).any() or (
        (nodes2["id:ID"] == common_application_node_id)
        & (nodes2[":LABEL"] == common_application_node_label)
    ).any()

    if not common_node_exists:
        common_application_node = create_node(
            node_id=common_application_node_id,
            label=common_application_node_label,
            full_name=common_application_node_id,
            simple_name=common_application_node_id,
            color="#cccccc",
        )
        nodes1.loc[len(nodes1)] = common_application_node

        domain_node = nodes1[(nodes1[":LABEL"] == "Domain")]

        component_containment_edge = create_edge(
            domain_node.iloc[0]["id:ID"], common_application_node_id, "CONTAINS"
        )
        edges1.loc[len(edges1)] = component_containment_edge

    return nodes1, edges1


def handle_common_global_namespace(nodes1, nodes2, edges1):
    common_glb_namespace_node_id = "pkg:Common-global-namespace"
    common_node_exists = (
        (nodes1["id:ID"] == common_glb_namespace_node_id)
        & (nodes1[":LABEL"] == "Component")
    ).any() or (
        (nodes2["id:ID"] == common_glb_namespace_node_id)
        & (nodes2[":LABEL"] == "Component")
    ).any()

    if not common_node_exists:
        common_glb_namespace_component = create_node(
            node_id=common_glb_namespace_node_id,
            label="Component",
            full_name=common_glb_namespace_node_id.removeprefix("pkg:"),
            simple_name=common_glb_namespace_node_id.removeprefix("pkg:"),
            color="#cccccc",
        )

        common_glb_namespace_component = create_node(
            node_id=common_glb_namespace_node_id,
            label="Component",
            full_name=common_glb_namespace_node_id.removeprefix("pkg:"),
            simple_name=common_glb_namespace_node_id.removeprefix("pkg:"),
            color="#cccccc",
        )

        common_glb_namespace_sublayer = create_node(
            node_id=common_glb_namespace_node_id.removeprefix("pkg:"),
            label="Sublayer",
            full_name=common_glb_namespace_node_id.removeprefix("pkg:"),
            simple_name=common_glb_namespace_node_id.removeprefix("pkg:"),
            color="#cccccc",
        )
        nodes1.loc[len(nodes1)] = common_glb_namespace_component
        nodes1.loc[len(nodes1)] = common_glb_namespace_sublayer

        component_containment_edge = create_edge(
            "Common", common_glb_namespace_node_id, "CONTAINS"
        )
        sublayer_containment_edge = create_edge(
            common_glb_namespace_node_id,
            common_glb_namespace_node_id.removeprefix("pkg:"),
            "CONTAINS",
        )

        edges1.loc[len(edges1)] = component_containment_edge
        edges1.loc[len(edges1)] = sublayer_containment_edge

    return nodes1, edges1


def handle_common_components(common_components, edges1, edges2):
    updated_edges1 = edges1.copy()
    updated_edges2 = edges2.copy()

    def process_component(component_id):
        nonlocal updated_edges1, updated_edges2
        updated_edges1, updated_edges2 = handle_common_node_parent(
            component_id, updated_edges1, updated_edges2, "Common"
        )
        return updated_edges1, updated_edges2

    common_components["id:ID"].apply(process_component)
    return updated_edges1, updated_edges2



def handle_common_modules(common_modules, edges1, edges2):
    """
    Process `common_modules` to check for common parents and handle common nodes without explicit iteration.

    Args:
        common_modules (pd.DataFrame): DataFrame containing module information, with "id:ID" as a column.
        edges1 (pd.DataFrame): First dataframe containing edge data.
        edges2 (pd.DataFrame): Second dataframe containing edge data.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Updated edges1 and edges2 DataFrames.
    """
    updated_edges1 = edges1.copy()
    updated_edges2 = edges2.copy()

    def process_module(component_id):
        nonlocal updated_edges1, updated_edges2
        has_same_parent, in_global_namespace = compare_for_same_parent(component_id, updated_edges1, updated_edges2)
        if in_global_namespace and not has_same_parent:
            updated_edges1, updated_edges2 = handle_common_node_parent(
                component_id, updated_edges1, updated_edges2, "Common-global-namespace"
            )
        return updated_edges1, updated_edges2

    common_modules["id:ID"].apply(process_module)

    return updated_edges1, updated_edges2

def merge_nodes_and_edges(
    nodes1_path,
    nodes2_path,
    edges1_path,
    edges2_path,
    separateCommon,
    nodes3_name,
    output_folder,
):
    # Load nodes and edges from CSV files
    nodes1 = pd.read_csv(nodes1_path)
    nodes2 = pd.read_csv(nodes2_path)
    edges1 = pd.read_csv(edges1_path)
    edges2 = pd.read_csv(edges2_path)

    # Initialize common_nodes and "Common" node handling
    common_nodes = []
    if separateCommon:

        # Identify common nodes
        common_nodes = nodes1.merge(nodes2, on=["id:ID", ":LABEL"], how="inner")
        common_nodes_list = common_nodes[["id:ID", ":LABEL"]]
        common_components = common_nodes_list[
            common_nodes_list[":LABEL"] == "Component"
        ]

        print(common_components)
        common_modules = common_nodes_list[common_nodes_list[":LABEL"] == "Module"]
        common_nodes_list = common_nodes_list.set_index([":LABEL"])
        common_components = common_nodes_list.loc["Component"]
        common_modules = common_nodes_list.loc["Module"]

        nodes1, edges1 = handle_common_application_node(nodes1, nodes2, edges1)

        edges1, edges2 = handle_common_components(common_components, edges1, edges2)

        edges1, edges2 = handle_common_modules(common_modules, edges1, edges2)
        nodes1, edges1 = handle_common_global_namespace(nodes1, nodes2, edges1)

    # Merge nodes, keeping all unique nodes
    unified_nodes = (
        pd.concat([nodes1, nodes2])
        .drop_duplicates(subset=["id:ID"])
        .reset_index(drop=True)
    )

    # Merge edges, ensuring no duplicates
    unified_edges = (
        pd.concat([edges1, edges2])
        .drop_duplicates(subset=[":START_ID", ":END_ID", ":TYPE"])
        .reset_index(drop=True)
    )

    # Calculate duplicates for nodes and edges
    duplicate_nodes_count = len(nodes1) + len(nodes2) - len(unified_nodes)
    duplicate_edges_count = len(edges1) + len(edges2) - len(unified_edges)

    # Output merged nodes and edges to CSV
    unified_nodes.to_csv(output_folder + f"{nodes3_name}-nodes.csv", index=False)
    unified_edges.to_csv(output_folder + f"{nodes3_name}-edges.csv", index=False)

    # Print duplicate counts
    print(f"Duplicate nodes: {duplicate_nodes_count}")
    print(f"Duplicate edges: {duplicate_edges_count}")

    # If `separateCommon` is true, print common nodes for verification
    if separateCommon:
        print(f"Common nodes: {len(common_nodes)}")
