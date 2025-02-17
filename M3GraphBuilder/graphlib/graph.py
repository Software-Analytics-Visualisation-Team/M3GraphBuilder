import json
from collections.abc import Iterable
from typing import Optional, List, Dict, Union, Set, Tuple


def create_node(
    node_id: str,
    label: str,
    full_name: str,
    simple_name: str,
    color: str,
    dep_profile_cat=None,
    cohesion=None,
) -> tuple:
    return (node_id, label, full_name, simple_name, color, dep_profile_cat, cohesion)


def create_edge(
    edge_source: str, edge_target: str, edge_label: str, properties=None
) -> tuple:
    return (
        f"{edge_source}-{edge_label}-{edge_target}",
        edge_label,
        edge_source,
        edge_target,
        "{}",
        None,
        None,
        None,
    )


class Node:
    def __init__(self, _id, *labels, **properties):
        self.id = _id
        self.labels = set(labels)
        self.properties = properties

    def to_dict(self):
        return {
            "data": {
                "id": self.id,
                "labels": list(self.labels),
                "properties": self.properties,
            }
        }

    def __str__(self):
        return json.dumps(self.to_dict())


class Edge:
    def __init__(self, source, target, labels, **properties):
        self.id = f"{source}-{labels[0]}-{target}"
        self.source = source
        self.target = target
        self.labels = labels
        self.properties = properties

    def to_dict(self):
        return {
            "data": {
                "id": self.id,
                "source": self.source,
                "target": self.target,
                "labels": self.labels,
                "properties": self.properties,
            }
        }

    def __str__(self):
        return json.dumps(self.to_dict())


def invert(edge_list: List[Edge], new_label: Optional[str] = None) -> List[Edge]:
    """
    Inverts the direction of edges in the given edge list.

    Args:
            edge_list (list): A list of edges to invert.
            new_label (str, optional): A new label for the inverted edges. Defaults to None.

    Returns:
            list: A list of inverted edges with updated label.
    """
    return [
        Edge(
            source=edge.target,
            target=edge.source,
            labels=new_label if new_label else f"inv_{edge.labels[0]}",
            **edge.properties,
        )
        for edge in edge_list
    ]


def compose(
    edges1: List[Edge], edges2: List[Edge], new_label: Optional[str] = None
) -> List[Edge]:
    """
    Composes two lists of edges.

    Args:
            edges1 (list): The first list of edges.
            edges2 (list): The second list of edges.
            new_label (str, optional): A new label for the composed edges. Defaults to None.

    Returns:
            list: A list of composed edges.
    """
    mapping = {
        edge.source: {
            "target": edge.target,
            "labels": edge.labels[0],
            "weight": edge.properties.get("weight", 1),
        }
        for edge in edges2
    }
    composed_edges = []
    for edge in edges1:
        if edge.target in mapping:
            new_weight = mapping[edge.target]["weight"] * edge.properties.get(
                "weight", 1
            )
            composed_edge = Edge(
                source=edge.source,
                target=mapping[edge.target]["target"],
                labels=(
                    new_label
                    if new_label
                    else f"{edge.labels[0]},{mapping[edge.target]['labels']}"
                ),
                weight=new_weight,
            )
            composed_edges.append(composed_edge)
    return composed_edges


def lift(
    edges1: List[Edge], edges2: List[Edge], new_label: Optional[str] = None
) -> List[Edge]:
    """
    Lifts relations by composing two lists of edges and their inverses.

    Args:
            edges1 (list): The first list of edges.
            edges2 (list): The second list of edges.
            new_label (str, optional): A new label for the lifted edges. Defaults to None.

    Returns:
            list: A list of lifted edges.
    """
    return compose(compose(edges1, edges2), invert(edges1), new_label)


def triplets(
    edge_list1: List[Edge], edge_list2: List[Edge]
) -> Set[Tuple[str, str, str]]:
    source_mapping = {edge.target: edge.source for edge in edge_list1}

    paths = set()
    for edge in edge_list2:
        if edge.source in source_mapping:
            source1 = source_mapping[edge.source]
            triplet = (source1, edge.source, edge.target)
            paths.add(triplet)

    return paths


class Graph:
    """
    A class to represent a graph with nodes and edges.

    Attributes:
            nodes (dict): A dictionary of nodes.
            edges (dict): A dictionary of edges categorized by label.
    """

    def __init__(self, graph_data: dict) -> None:
        """
        Initializes the Graph with nodes and edges from the provided data.

        Args:
                graph_data (dict): A dictionary containing graph data with nodes and edges.
        """
        self.nodes: Dict[str, Node] = {
            node["data"]["id"]: Node(
                node["data"]["id"],
                *node["data"]["labels"],
                **node["data"]["properties"],
            )
            for node in graph_data["elements"]["nodes"]
        }
        self.edges: Dict[str, List[Edge]] = {}
        for edge in graph_data["elements"]["edges"]:
            edge_data = edge["data"]
            edge_obj = Edge(
                edge_data["source"],
                edge_data["target"],
                edge_data["labels"][0],
                **edge_data["properties"],
            )
            if edge_obj.labels not in self.edges:
                self.edges[edge_obj.labels] = []
            self.edges[edge_obj.labels].append(edge_obj)

    def invert_edges(self, edge_label: str, new_label: Optional[str] = None) -> None:
        """
        Inverts the edges with the specified label and saves them under a new label.

        Args:
                edge_label (str): The label of the edges to invert.
                new_label (str, optional): The label for the inverted edges. Defaults to None.
        """
        if edge_label in self.edges:
            inverted = invert(self.edges[edge_label], new_label)
            new_label = new_label or f"inv_{edge_label}"
            self.edges[new_label] = inverted

    def compose_edges(
        self, edge_label1: str, edge_label2: str, new_label: Optional[str] = None
    ) -> None:
        """
        Composes edges with the specified label and saves them under a new label.

        Args:
                edge_label1 (str): The label of the first list of edges.
                edge_label2 (str): The label of the second list of edges.
                new_label (str, optional): The label for the composed edges. Defaults to None.
        """
        if (edge_label1 in self.edges) and (edge_label2 in self.edges):
            new_label = new_label or f"{edge_label1}_{edge_label2}"
            composed = compose(
                self.edges[edge_label1], self.edges[edge_label2], new_label
            )
            self.edges[new_label] = composed

    def lift_edges(
        self, edge_label1: str, edge_label2: str, new_label: Optional[str] = None
    ) -> None:
        """
        Lifts relations by composing edges with the specified label and their inverses, then saves them under a new label.

        Args:
                edge_label1 (str): The label of the first list of edges.
                edge_label2 (str): The label of the second list of edges.
                new_label (str, optional): The label for the lifted edges. Defaults to None.
        """
        if (edge_label1 in self.edges) and (edge_label2 in self.edges):
            lifted = lift(self.edges[edge_label1], self.edges[edge_label2], new_label)
            new_label = new_label or f"lifted_{edge_label1}_{edge_label2}"
            self.edges[new_label] = lifted

    def filter_nodes_by_labels(
        self, label: Union[List[str], Set[str]]
    ) -> Dict[str, Node]:
        """
        Filters nodes by the specified label.

        Args:
                label (list or set): A list of label to filter nodes by.

        Returns:
                dict: A dictionary of filtered nodes.
        """
        return {
            key: node
            for key, node in self.nodes.items()
            if any(label in label for label in node.label)
        }

    def get_all_node_labels(self) -> Set[str]:
        """
        Retrieves all unique node label present in the graph.

        Returns:
                set: A set of all node label.
        """
        return {label for node in self.nodes.values() for label in node.label}

    def get_all_edge_labels(self) -> Set[str]:
        """
        Retrieves all unique edge label present in the graph.

        Returns:
                set: A set of all edge label.
        """
        return set(self.edges.keys())

    def get_edges_with_node_labels(
        self, edge_label: str, node_label: str
    ) -> List[Edge]:
        """
        Retrieves edges whose source and target nodes have the specified label.

        Args:
                edge_label (str): The label of the edges to retrieve.
                node_label (str): The label of the nodes to filter by.

        Returns:
                list: A list of edges that match the criteria.
        """
        if edge_label in self.edges:
            return [
                edge
                for edge in self.edges[edge_label]
                if (node_label in self.nodes[edge.source].label)
                and (node_label in self.nodes[edge.target].label)
            ]
        return []

    def get_edge_node_labels(self, edge: Edge) -> List[Tuple[str, str]]:
        """
        Retrieves the label of the source and target nodes for a given edge.

        Args:
                edge (Edge): The edge to retrieve node label for.

        Returns:
                list: A list of tuples containing source and target node label.
        """
        source_labels = self.nodes.get(edge.source, Node(None)).label
        target_labels = self.nodes.get(edge.target, Node(None)).label
        return [
            (source_label, target_label)
            for source_label in source_labels
            for target_label in target_labels
        ]

    def get_source_and_target_labels(self, edge_label: str) -> Set[str]:
        """
        Retrieves the set of source and target label for a given list of edges.

        Args:
                edge_label (str): The label of the edges to retrieve label for.

        Returns:
                set: A set of source and target label.
        """
        edge_node_labels: Set[str] = {
            label
            for edge in self.edges[edge_label]
            for label in self.get_edge_node_labels(edge)
        }
        return edge_node_labels

    def generate_ontology(self) -> Dict[str, Set[str]]:
        """
        Generates an ontology from the graph's edges and nodes.

        Returns:
                dict: A dictionary representing the ontology.
        """
        return {label: self.get_source_and_target_labels(label) for label in self.edges}

    def find_nodes(self, label=None, where=None) -> List[Node]:
        return [
            node
            for node in self.nodes.values()
            if (not label or label in node.label) and (not where or where(node))
        ]

    def find_edges(
        self,
        label=None,
        source_label=None,
        target_label=None,
        where_edge=None,
        where_source=None,
        where_target=None,
    ):
        if label:
            edge_list = self.edges.get(label, [])
        else:
            edge_list = [edge for edges in self.edges.values() for edge in edges]

        return [
            edge
            for edge in edge_list
            if (not source_label or source_label in self.nodes[edge.source].label)
            and (not target_label or target_label in self.nodes[edge.target].label)
            and (not where_edge or where_edge(edge))
            and (not where_source or where_source(self.nodes[edge.source]))
            and (not where_target or where_target(self.nodes[edge.target]))
        ]

    def clean_up(self):
        for edge_type in list(self.edges.keys()):
            self.edges[edge_type] = [
                edge
                for edge in self.edges[edge_type]
                if edge.source in self.nodes and edge.target in self.nodes
            ]

    def __str__(self):
        return json.dumps(self.to_dict())

    def to_dict(
        self, *args: str, node_labels: Optional[Union[str, Iterable[str]]] = None
    ) -> dict:
        """
        Converts the graph into a dictionary format with specified edge and node label.

        Args:
                *args: Variable length argument list of edge label to include.
                node_labels (str or iterable, optional): label of nodes to include. Defaults to None.

        Returns:
                dict: A dictionary representation of the graph with specified elements.
        """
        included_edge_labels = list(args) if args else list(self.edges.keys())

        if node_labels == "all":
            included_node_labels = self.get_all_node_labels()
        else:
            included_node_labels: Set[str] = {
                node_label
                for edge_label in included_edge_labels
                for node_label_pair in self.get_source_and_target_labels(edge_label)
                for node_label in node_label_pair
            }
            if isinstance(node_labels, str):
                included_node_labels.add(node_labels)
            elif isinstance(node_labels, Iterable):
                included_node_labels.update(node_labels)

        included_nodes: Dict[str, Node] = self.filter_nodes_by_labels(
            included_node_labels
        )

        included_edges: Dict[str, List[Edge]] = {
            label: edge_list
            for label, edge_list in self.edges.items()
            if label in included_edge_labels
        }

        return {
            "elements": {
                "nodes": [
                    {"data": node.to_dict()["data"]} for node in included_nodes.values()
                ],
                "edges": [
                    {"data": edge.to_dict()["data"]}
                    for edge in sum(included_edges.values(), [])
                ],
            }
        }
