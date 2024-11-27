from M3GraphBuilder.graphlib.graph import Graph, Edge, invert, lift
import json
import csv
import os
from collections import defaultdict

class Arvisaninator:
    data = {}
    config = {}
    domain_name = ""
    domain_desc = ""
    application_name = ""
    roleStereotypeColors = {
    "Unknown": "#cccccc",
    "Controller": "#decbe4",
    "Coordinator": "#ccebc5",
    "Information Holder": "#fbb4ae",
    "Interfacer": "#fed9a6",
    "User Interfacer": "#fed9a6",
    "Internal Interfacer": "#fed9a6",
    "External Interfacer": "#fed9a6",
    "Service Provider": "#b3cde3",
    "Structurer": "#fddaec",
    }
    dependencyProfiles = {}

    def __init__(self, config, graph_path, output_path) -> None:
        def get_filename_without_extension(graph_path):
            # Extract the filename with extension
            filename_with_ext = os.path.basename(graph_path)
            
            # Remove the specific ".lpg.json" extension if it exists
            if filename_with_ext.endswith(".lpg.json"):
                filename_without_ext = filename_with_ext[:-len(".lpg.json")]
            else:
                # If the extension is not ".lpg.json", return the filename as-is
                filename_without_ext = os.path.splitext(filename_with_ext)[0]
            
            return filename_without_ext

        with open(graph_path, "r") as graph:
            json_file = json.load(graph)

        self.data = Graph(json_file)
        self.config = config
        self.output_path = output_path
        self.domain_name = config['project']['name']
        self.project_desc = config['project']['desc']
        self.application_name = get_filename_without_extension(graph_path)

    def create_node(self, node_id: str, label: str, full_name: str, simple_name: str, color: str, dep_profile_cat=None, cohesion=None) -> tuple:
        return (node_id, label, full_name, simple_name, color, dep_profile_cat, cohesion)
    
    def create_edge(self, edge_source: str, edge_target: str, edge_label: str, properties=None) -> tuple:
        return (f"{edge_source}-{edge_label}-{edge_target}", edge_label, edge_source, edge_target, "{}", None, None, None)
    
    def create_domain_node(self):
        return self.create_node(
            node_id=self.domain_name,
            label="Domain",
            full_name=self.domain_name,
            simple_name=self.domain_name,
            color="#666666",
            dep_profile_cat=self.dependencyProfiles.get(self.domain_name, None)
        )
    
    def create_application_node(self):
        return self.create_node(
            node_id=self.application_name,
            label="Application",
            full_name=self.application_name,
            simple_name=self.application_name,
            color="#666666",
            dep_profile_cat=self.dependencyProfiles.get(self.application_name, None)
        )
    
    def create_component_nodes(self, components: list[str]) -> list[tuple[str, str, str, str, str,  None, None]]:
        """
        Creates a list of component nodes containing all extracted components, and a global namespace component.

        Returns:
            list: A list of component names derived from top-level namespaces.
        """
         
        default_color = "#666666"
        label = "Component"

        # Create nodes for each component
        nodes = [
            self.create_node(
                node_id=f'pkg:{component}',
                label=label,
                full_name=component,
                simple_name=component,
                color=default_color,
                dep_profile_cat=self.dependencyProfiles.get(component, None)
            )
            for component in components
        ]

        return nodes
    
    
    def create_sublayer_nodes(self, sublayers):
        """
        Creates a list of sublayer nodes from the namespaces in the graph.

        Returns:
            list: A list of sublayer nodes.
        """        
        layer_colors = {	
            'Presentation Layer': '#ee3239',
            'Service Layer': '#fece00',
            'Domain Layer': '#5eaa5f',
            'Data Source Layer': '#6a6dba',
            'Unknown': '#666666'
        }
        return [
            self.create_node(
                node_id=sublayer,
                label="Sublayer",
                full_name=sublayer,
                simple_name=sublayer,
                color=layer_colors[self.data.nodes[sublayer].properties.get('layer', 'Unknown') if self.data.nodes.get(sublayer) else 'Unknown'],
                dep_profile_cat=self.dependencyProfiles.get(sublayer, None)
            )
            for sublayer in sublayers
        ]
    
    def create_module_nodes(self, contained_structures, orphan_structures):

        modules =  [self.create_node(node_id= node, label="Module", full_name=node, simple_name= self.data.nodes[node].properties['simpleName'], color= self.roleStereotypeColors[self.data.nodes[node].properties.get('roleStereotype', 'Unknown')], dep_profile_cat=self.dependencyProfiles.get(id, None))
                    for node in contained_structures]
        
        orphaned_modules = [
            self.create_node(node_id= node, label="Module", full_name=node, simple_name= self.data.nodes[node].properties['simpleName'], color= self.roleStereotypeColors[self.data.nodes[node].properties.get('roleStereotype', 'Unknown')], dep_profile_cat=self.dependencyProfiles.get(id, None))
            for node in orphan_structures]

        return modules, orphaned_modules

    
    def extract_sublayers(self):
       
        sublayers = {
            edge.source
            for edge in self.data.edges.get('contains', [])
            if 'Container' in self.data.nodes[edge.source].labels
        }

        sublayers.add("global-namespace")

        return sublayers
    
    def extract_structures(self):
        contained_structures = {
            edge.target
            for edge in self.data.edges['contains']
            if 'Container' in self.data.nodes[edge.source].labels
                and 'Structure' in self.data.nodes[edge.target].labels
        }

        orphan_structures = {
            node
            for node in self.data.nodes
            if 'Structure' in self.data.nodes[node].labels
                and node not in contained_structures
            }
    
        return contained_structures, orphan_structures
    
    def extract_components(self, sublayers):
        """
        Extracts top-level namespaces to be treated as components.

        Returns:
            list: A list of component names derived from top-level namespaces,
            list: A list containing a map between sublayers and components.
        """
        # Determine full namespace paths for each namespace
        namespace_paths = [
            self.find_path_from_root(self.data.edges['contains'], namespace_id)
            for namespace_id in sublayers
        ]

        # Extract and return top-level namespaces
        top_level_namespaces = self.extract_top_level_namespaces(namespace_paths)
        sublayer_to_component = self.create_mapping(namespace_paths, top_level_namespaces)


        return [namespace[-1] for namespace in top_level_namespaces], sublayer_to_component

    def compute_dependency_profiles(self, edges_calls):
        """
        Computes dependency profiles for given edges.
        """
        def dep_profile(inbound, outbound):
            if inbound == 0 and outbound > 0:
                return "outbound"
            elif inbound > 0 and outbound == 0:
                return "inbound"
            elif inbound > 0 and outbound > 0:
                return "transit"
            return "hidden"

        # Get parent mapping
        parents = {e.source: e.target for e in invert(self.data.edges.get('contains', []))}
        
        dependency_profiles = defaultdict(list)

        for edge in edges_calls:
            src_id, tgt_id = edge.source, edge.target
            if parents.get(src_id) and parents.get(tgt_id) and parents[src_id] != parents[tgt_id]:
                dependency_profiles[src_id].append('out')
                dependency_profiles[tgt_id].append('in')

        # Count occurrences of 'in' and 'out' for each node
        dependency_counts = {
            node_id: {
                "in": profile.count("in"),
                "out": profile.count("out")
            }
            for node_id, profile in dependency_profiles.items()
        }
        
        # Classify dependency profiles based on counts
        return {
            node_id: dep_profile(profile["in"], profile["out"])
            for node_id, profile in dependency_counts.items()
        }

    def find_path_from_root(self, tree, target_node):
			# Step 1: Build a dictionary to map each node to its parent
            parent_map = {}
            for edge in tree:
                parent_map[edge.target] = edge.source

			# Step 2: Trace the path from target_node to the root
            path = []
            current_node = target_node
            while current_node in parent_map:
                path.append(current_node)
                current_node = parent_map[current_node]

            # Step 3: Append the root node to the path
            if current_node is not None:
                path.append(current_node)

            # Step 4: Reverse the path to get root to target_node order
            path.reverse()

            return tuple(path)
    
    def extract_top_level_namespaces(self, namespace_paths: list[list[str]]) -> list[tuple[str]]:
        """
        Extracts unique top-level namespaces.
        """
        unique_prefixes = {tuple(path[:-1]) if len(path) > 1 else tuple(path) for path in namespace_paths}
        sorted_prefixes = sorted(unique_prefixes, key=len)

        results = []
        for prefix in sorted_prefixes:
            if not any(prefix[:len(existing)] == existing for existing in results):
                results.append(prefix)
        return results
    
    def create_mapping(self, list1, list2):
        mapping = dict()
        for tup in list1:
            key = tup[-1]  # Last element of the tuple as the key
            for tup2 in list2:
                if tuple(tup[:len(tup2)]) == tup2:  # Match the prefix part in list1 with list2
                    mapping[key] = f'pkg:{tup2[-1]}'
                    break
        return mapping
    
    
    def create_contains_edges(self, components, sublayers, sublayer_to_component, orphan_modules, package_modules):
        """
        Creates edges that define CONTAINS relationships between the domain, application and components, 

        Args:
            components (list[str]): A list of component names to create containment edges for.

        Returns:
            list[tuple]: A list of edges, where each edge is represented by a tuple
        """
        contains_edge_label = "CONTAINS"
        # Create edges for domain and application
        containment_edges = [
            self.create_edge(self.domain_name, self.application_name, contains_edge_label),
        ]

        # Create containment edges for components
        containment_edges.extend(
            self.create_edge(self.application_name, f'pkg:{component}', contains_edge_label)
            for component in components
        )

        # Create containment edge for global namespace
        containment_edges.append(
            self.create_edge(self.application_name, 'pkg:global-namespace', contains_edge_label)
        )

        # Create containment edge for sublayers (from components)
        containment_edges.extend(
            self.create_edge(sublayer_to_component[id], id, contains_edge_label)
            for id in sublayers
        )

        # Create containment edge from the global-namespace sublayer to all modules that do not have a parent.
        containment_edges.extend(
            self.create_edge('global-namespace', id, contains_edge_label)
            for id in orphan_modules
        )

        # Create containment edge for modules (fromsublayers)
        containment_edges.extend(
            self.create_edge(edge.source, edge.target, contains_edge_label)
            for edge in self.data.edges['contains']
            if 'Container' in self.data.nodes[edge.source].labels and 'Structure' in self.data.nodes[edge.target].labels
        )

        # Create containment edge for modules (fromsublayers)
        containment_edges.extend(
            self.create_edge(module[0].removeprefix("mod:"), module[0], contains_edge_label)
            for module in package_modules
        )

        return containment_edges
    
    def create_calls_edges(self):
        """
        Creates edges that define CALLS relationships, handling both 'calls' and 'hasScript'/'invokes' edges.
        
        Returns:
            tuple: A tuple containing:
                - edges_calls (list): List of edges representing calls.
                - calls (list): List of call relationships formatted for export.
                - package_modules (set): Set of package modules.
        """
        def create_edge_from_data(edge, edge_type):
            """Helper function to create a new edge."""
            source = edge.source
            target = edge.target

            source_node = self.data.nodes.get(edge.source)
            if source_node and "Container" in source_node.labels:
                source = f"mod:{edge.source}"
                container_nodes.add(edge.source)

            target_node = self.data.nodes.get(edge.target)
            if target_node and "Container" in target_node.labels:
                target = f"mod:{edge.target}"
                container_nodes.add(edge.target)
            return Edge(source=source, target=target, labels=edge.labels, properties=edge.properties)

        # Initialize lists and sets
        hasScript_edges = []
        invokes_edges = []
        container_nodes = set()
        edges_calls = []

        # Check if 'calls' edges exist, else combine 'hasScript' and 'invokes'
        if self.data.edges.get('calls'):
            print("Found calls")
            edges_calls = self.data.edges['calls']
        else:
            print("No calls")
            # Handle 'hasScript' edges
            hasScript_edges = [
                create_edge_from_data(edge, 'hasScript') for edge in self.data.edges.get('hasScript', [])
            ]
            
            # Handle 'invokes' edges
            invokes_edges = [
                create_edge_from_data(edge, 'invokes') for edge in self.data.edges.get('invokes', [])
            ]
            
            # Combine edges
            edges_calls = lift(hasScript_edges, invokes_edges)

        # ("id", ":TYPE", ":START_ID", ":END_ID", "references", "dependencyTypes", "nrDependencies:INT", "nrCalls:INT")
        package_modules = set()
        calls = []
        
        for edge in edges_calls:
            if edge.source != edge.target:
                # Check if source or target starts with "mod:"
                if edge.source.startswith("mod:"):
                    node_id = edge.source.removeprefix("mod:")
                    package_modules.add(
                        self.create_node(
                            node_id=edge.source,
                            label="Module",
                            full_name=edge.source,
                            simple_name=self.data.nodes[node_id].properties["simpleName"],
                            color=self.roleStereotypeColors.get(node_id, "Unknown"),
                            dep_profile_cat=self.dependencyProfiles.get(node_id, None))
                    )
                if edge.target.startswith("mod:"):
                    node_id = edge.target.removeprefix("mod:")
                    package_modules.add(
                        self.create_node(
                            node_id=edge.target,
                            label="Module",
                            full_name=edge.target,
                            simple_name=self.data.nodes[node_id].properties["simpleName"],
                            color=self.roleStereotypeColors.get(node_id, "Unknown"),
                            dep_profile_cat=self.dependencyProfiles.get(node_id, None))
                        )
                    
                # Add the call to the list
                calls.append((
                    f'{edge.source}-calls-{edge.target}',
                    'CALLS',
                    edge.source,
                    edge.target,
                    "{}",
                    "compile_time",
                    edge.properties.get('weight', 0),
                    None
                ))

        return edges_calls, calls, package_modules


    def export(self):
        """
        Exports nodes and edges to CSV files.
        """
        def generate_nodes_and_edges():

            edge_data, calls_edges, package_modules = self.create_calls_edges()

            self.dependencyProfiles = self.compute_dependency_profiles(edge_data)
            
            #TODO: Find suitable name for edge_data
        
            sublayers = self.extract_sublayers()
            components, sublayer_to_component = self.extract_components(sublayers)
            contained_structures, orphan_structures = self.extract_structures()
            modules, orphan_modules = self.create_module_nodes(contained_structures, orphan_structures)
            
            nodes = [
                self.create_domain_node(),
                self.create_application_node(),
                *self.create_component_nodes(components),
                *self.create_sublayer_nodes(sublayers),
                *modules,
                *orphan_modules,
                *package_modules,
            ]

            contains_edges = self.create_contains_edges(components, sublayers, sublayer_to_component, orphan_structures, package_modules)
            edges = contains_edges
            edges += calls_edges

            return nodes, edges

        def write_to_csv(filename, header_row, rows):
            with open(self.output_path + filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(header_row)
                writer.writerows(rows)

        nodes, edges = generate_nodes_and_edges()

        node_header = ("id:ID",":LABEL","fullName","simpleName","color","dependencyProfileCategory","cohesion")
        edge_header = ("id",":TYPE",":START_ID",":END_ID","references","dependencyTypes","nrDependencies:INT","nrCalls:INT")

        write_to_csv(f"{self.domain_name}-{self.application_name}-nodes.csv", node_header, nodes)
        write_to_csv(f"{self.domain_name}-{self.application_name}-edges.csv", edge_header, edges)