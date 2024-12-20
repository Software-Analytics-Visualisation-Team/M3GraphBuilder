from copy import deepcopy
import json
import M3GraphBuilder.converters.constants as constants
import M3GraphBuilder.converters.m3_utils as m3_utils
import logging

class Cpp:
    primitives = ["int", "double", "float", "void", "char", "string", "boolean"]
    lpg = {"elements": {"nodes": [], "edges": []}}
    parsed = None
    path = None
    containers = {}
    structures = {}
    containers_structures_simple_names = {}
    scripts = {}

    def __init__(self, path, parsed, verbose, issues=None) -> None:
        self.path = path
        self.parsed = parsed
        self.verbose = verbose
        self.issues = issues

    def add_edges(self, kind, content):
        edge_id = {}
        source = {}
        properties = {"weight": 1}
        target = {}
        labels = [kind]

        match kind:
            case "hasScript":
                edge_id = hash(content[0] + content[1].get("fullLoc"))
                source = content[1].get("parent")
                target = content[1].get("fullLoc")

            case "specializes":
                for base_fragment in content[1]["extends"]:
                    edge_id = hash(content[0]) + hash(base_fragment.get("fullLoc"))
                    source = base_fragment.get("fullLoc")
                    target = content[1].get("fullLoc")

            case "invokes":
                edge_id = hash(content[1].get("id"))
                source = content[1]["source"].get("fullLoc")
                target = content[1]["target"].get("fullLoc")
                properties = {"weight": content[1]["weight"]}

            case "contains-definition":
                edge_id = hash(content["translationUnit"] + "" + content["definition"])
                source = content["translationUnit"]
                target = content["definition"]
                labels = ["specializes"]

            case "contains":
                try:
                    if content[1].get("fragmentType") in constants.CONTAINER_PARENTS:
                        contained_fragments = content[1].get("contains")
                        if contained_fragments is not None:

                            for child_fragment in contained_fragments:
                                edge_id = hash(content[0]) + hash(
                                    child_fragment.get("fullLoc")
                                )
                                source = content[1].get("fullLoc")
                                target = child_fragment.get("fullLoc")

                                self.append_edge(
                                    edge_id, source, properties, target, labels
                                )
                            edge_id = None

                    elif (
                        content[1].get("fragmentType") is constants.M3_CPP_METHOD_TYPE
                        and content[1].get("location") is not None
                    ):
                        try:
                            edge_id = (
                                hash(content[1]["class"])
                                + hash(content[0])
                                + hash(content[1]["location"].get("file"))
                            )
                            source = content[1]["location"].get("file")
                            target = content[0]
                        except:
                            logging.info(
                                f"Failed adding contains relationship between {source} and {target}"
                            )
                            logging.info("Trying backup.")
                            source = next(
                                item
                                for item in self.lpg["elements"]["edges"]
                                if item["data"]["target"] == content[1]["class"]
                                and "contains" in item["data"]["labels"]
                            )

                            if source is not None:
                                edge_id = (
                                    hash(content[1]["class"])
                                    + hash(content[0])
                                    + hash(source["data"]["source"])
                                )
                                source = source["data"]["source"]
                                target = content[0]
                            else:
                                logging.info(
                                    f"Failed to add a contains edge for {content}"
                                )
                                return

                except Exception as e:
                    logging.info("Problem adding 'contains' relationship for ", content)

        if edge_id and source and properties and target and labels:
            self.append_edge(edge_id, source, properties, target, labels)

    def append_node(self, node_id, properties, labels):
        try:
            self.lpg["elements"]["nodes"].append(
                {"data": {"id": node_id, "properties": properties, "labels": labels}}
            )
        except Exception as e:
            logging.info(f"Problem adding {labels} node relationship for ", node_id)
            logging.info(e)

    def append_edge(self, edge_id, source, properties, target, labels):
        try:
            self.lpg["elements"]["edges"].append(
                {
                    "data": {
                        "id": edge_id,
                        "source": source,
                        "properties": properties,
                        "target": target,
                        "labels": labels,
                    }
                }
            )
        except Exception as e:
            logging.info(f"Problem adding edge with id: {edge_id} to the graph")
            logging.info(e)

    def add_nodes(self, kind, content):
        node_id = {}
        properties = {}
        labels = []
        location = (
            content[1]["phyiscalLoc"]["loc"]
            if content[1].get("phyiscalLoc") is not None
            else content[1]["loc"]
        )

        match kind:
            case "macro":
                node_id = content[1].get("fullLoc")
                properties = {
                    "simpleName": content[1].get("loc"),
                    "description": "\n".join(
                        f"{file_path}: {count}"
                        for file_path, count in content[1].get("fileExpansions").items()
                    ),
                    "kind": "macro",
                }
                labels = ["Structure"]

            case "translation_unit":
                node_id = content[1].get("fullLoc")
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "description": content[1].get("physicalLoc"),
                    "kind": "translation_unit",
                }
                labels = ["Structure"]

            case "function":
                node_id = content[1].get("fragmentType") + ":" + content[1].get("loc")
                properties = {
                    "simpleName": content[1]["simpleName"],
                    "description": location,
                    "kind": kind,
                }
                labels = ["Operation"]

            case "method":
                node_id = content[1].get("fragmentType") + ":" + content[1].get("loc")
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "kind": kind,
                    "description": location,
                }
                labels = ["Operation"]

            case (
                "class"
                | "template"
                | "template_type"
                | "specialization"
                | "partial_specialization"
                | "deferred_class"
            ):
                node_id = content[1].get("fullLoc")
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "kind": kind,
                    "description": location,
                }
                labels = ["Structure"]

            case "namespace":
                node_id = content[1].get("fullLoc")
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "kind": "package",
                    "description": location,
                }
                labels = ["Container"]

        self.append_node(node_id, properties, labels)

    def get_fragment_files(self, fragments):
        function_Definitions_dict = m3_utils.parse_M3_function_Definitions(
            self.parsed, fragments
        )
        fragments_updated_from_Definitions = function_Definitions_dict.get("fragments")
        unlocated_fragments = function_Definitions_dict.get("unlocated_fragments")
        files_in_function_Definitions = function_Definitions_dict.get("files")

        if self.verbose:
            logging.info(
                f"[VERBOSE] Succesfully found the physical locations for {len(fragments_updated_from_Definitions) - len(unlocated_fragments)} fragments in 'functionDefinitions'."
            )
            logging.info(
                f"[VERBOSE] Did not find the physical locations of {len(unlocated_fragments)} fragments in 'functionDefinitions'."
            )

        if len(unlocated_fragments) > 0:
            logging.info(
                f"[VERBOSE] Searching for physical locations of unlocated fragments in 'declarations'."
            )

            declarations_dict = m3_utils.parse_M3_declarations(self.parsed, fragments)
            fragments_updated_from_Declarations = declarations_dict.get("fragments")
            still_unlocated_fragments = declarations_dict.get("unlocated_fragments")
            files_in_declarations = declarations_dict.get("files")

        if self.verbose:
            if len(still_unlocated_fragments) > 0:
                logging.info(
                    f"[VERBOSE] Succesfully found the physical locations for {len(fragments_updated_from_Declarations) - len(still_unlocated_fragments)} fragments in 'declarations'."
                )
                logging.info(
                    f"[VERBOSE] Did not find the physical locations of {len(still_unlocated_fragments)} fragments in 'declarations'."
                )
            else:
                logging.info(
                    f"[VERBOSE] Succesfully found the physical locations of all unlocated fragments in 'declarations'."
                )

        fragments_updated = (
            fragments_updated_from_Definitions | fragments_updated_from_Declarations
        )

        files = set()
        if len(files_in_function_Definitions) > 0:
            files.update(files_in_function_Definitions)
        if len(files_in_declarations) > 0:
            files.update(files_in_declarations)

        result = {"fragments": fragments_updated, "files": files}

        return result

    def add_namespaces(self, namespaces):
        logging.info("Adding namespaces")
        for n in namespaces.items():
            self.add_nodes("namespace", n)
            if n[1].get("contains") is not None:
                self.add_edges("contains", n)

        logging.info(f"Successfully added {len(namespaces)} namespaces to the graph.")

    def add_translation_units(self, translation_units):
        logging.info("Adding translation units")
        for tu in translation_units.items():
            self.add_nodes("translation_unit", tu)

            if tu[1].get("definitions") is not None:
                for definition in tu[1].get("definitions").items():
                    self.add_edges(
                        "contains-definition",
                        {"translationUnit": tu[0], "definition": definition[0]},
                    )

        logging.info(
            f"Successfully added {len(translation_units)} translation units to the graph."
        )

    def add_files(self, files):
        logging.info("Adding files")

        for file in files:
            self.add_nodes("file", file)

        logging.info(f"Successfully added {len(files)} files to the graph.")

    def add_classes(self, classes):
        logging.info("Adding classes")

        if self.verbose:
            logging.info(
                f"[VERBOSE] Updating declared locations for {len(classes)} classes."
            )

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, classes, constants.M3_CPP_CLASS_TYPE
        )
        classes_updated_from_Declarations = declarations_dict.get("fragments")

        updated_classes_with_extensions = m3_utils.parse_M3_extends(
            self.parsed, classes_updated_from_Declarations, constants.M3_CPP_CLASS_TYPE
        )
        for c in updated_classes_with_extensions.items():
            self.add_nodes("class", c)
            if c[1].get("extends") is not None:
                self.add_edges("specializes", c)
            self.add_edges("contains", c)

        logging.info(f"Successfully added {len(classes)} classes to the graph.")

    def add_deferred_classes(self, deferred_classes):
        logging.info("Adding deferred classes")

        if self.verbose:
            logging.info(
                f"[VERBOSE] Updating declared locations for {len(deferred_classes)} deferred classes."
            )

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, deferred_classes, constants.M3_CPP_DEFERRED_CLASS_TYPE
        )
        classes_updated_from_Declarations = declarations_dict.get("fragments")

        for c in classes_updated_from_Declarations.items():
            self.add_nodes("deferred_class", c)
            self.add_edges("contains", c)

        logging.info(
            f"Successfully added {len(deferred_classes)} deferredclasses to the graph."
        )

    def add_macros(self, macros):
        logging.info("Adding macros")

        for macro in macros.items():
            self.add_nodes("macro", macro)

        logging.info(f"Successfully added {len(macros)} macros to the graph.")

    def add_templates(self, templates):
        logging.info("Adding templates")

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, templates, constants.M3_CPP_CLASS_TEMPLATE_TYPE
        )
        templates_updated_from_Declarations = declarations_dict.get("fragments")

        updated_templates_with_extensions = m3_utils.parse_M3_extends(
            self.parsed,
            templates_updated_from_Declarations,
            constants.M3_CPP_CLASS_TEMPLATE_TYPE,
        )

        for temp in updated_templates_with_extensions.items():
            self.add_nodes("template", temp)

            if temp[1].get("extends") is not None:
                self.add_edges("specializes", temp)
            self.add_edges("contains", temp)

        logging.info(f"Successfully added {len(templates)} templates to the graph.")

    def add_template_types(self, template_types):
        logging.info("Adding template types")

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, template_types, constants.M3_CPP_TEMPLATE_TYPE_PARAM_LOC_SCM
        )
        template_types_updated_from_Declarations = declarations_dict.get("fragments")

        updated_template_types_with_extensions = m3_utils.parse_M3_extends(
            self.parsed,
            template_types_updated_from_Declarations,
            constants.M3_TEMPLATE_TYPE_PARAMETER_TYPE,
        )

        for temp_type in updated_template_types_with_extensions.items():
            self.add_nodes("template_type", temp_type)

            if temp_type[1].get("extends") is not None:
                self.add_edges("specializes", temp_type)
            self.add_edges("contains", temp_type)

        logging.info(
            f"Successfully added {len(template_types)} template types to the graph."
        )

    def add_specializations(self, specializations):
        logging.info("Adding specializations")

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, specializations, constants.M3_CPP_CLASS_SPECIALIZATION_TYPE
        )
        specializations_updated_from_Declarations = declarations_dict.get("fragments")
        updated_specializations_with_extensions = m3_utils.parse_M3_extends(
            self.parsed,
            specializations_updated_from_Declarations,
            constants.M3_CPP_CLASS_SPECIALIZATION_TYPE,
        )

        for spec in updated_specializations_with_extensions.items():
            self.add_nodes("specialization", spec)

            if spec[1].get("extends") is not None:
                self.add_edges("specializes", spec)
            self.add_edges("contains", spec)

        logging.info(
            f"Successfully added {len(specializations)} specializations to the graph."
        )

    def add_partial_specializations(self, partial_specializations):
        logging.info("Adding partial specializations")

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed,
            partial_specializations,
            constants.M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE,
        )
        partial_specializations_updated_from_Declarations = declarations_dict.get(
            "fragments"
        )

        updated_partial_specializations_with_extensions = m3_utils.parse_M3_extends(
            self.parsed,
            partial_specializations_updated_from_Declarations,
            constants.M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE,
        )

        for part_spec in updated_partial_specializations_with_extensions.items():
            self.add_nodes("partial_specialization", part_spec)

            if part_spec[1].get("extends") is not None:
                self.add_edges("specializes", part_spec)
            self.add_edges("contains", part_spec)

        logging.info(
            f"Successfully added {len(partial_specializations)} partial specializations to the graph."
        )

    def add_methods(self, methods):
        logging.info("Adding methods")

        for m in methods.items():
            self.add_nodes("method", m)

            parent_fragments_locs = self.containers_structures_simple_names.get(m[1]["parent"]).get("fullLocs")
            if parent_fragments_locs:
                
                for parent_loc in parent_fragments_locs:
                    m[1]["parent"] = parent_loc
                    self.add_edges("hasScript", m)

        logging.info(f"Successfully added {len(methods)} methods to the graph.")

    def add_functions(self, functions):
        logging.info("Adding functions")

        if self.verbose:
            logging.info(
                f"[VERBOSE] Updating declared locations for {len(functions)} functions."
            )

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, functions, constants.M3_CPP_FUNCTION_TYPE
        )
        functions_updated_from_Declarations = declarations_dict.get("fragments")

        for f in functions_updated_from_Declarations.items():
            self.add_nodes("function", f)
            if f[1]["parent"] in self.containers_structures_simple_names.keys():
                parent_fragment_loc = self.containers_structures_simple_names.get(f[1]["parent"]).get("fullLocs")[0]
                f[1]["parent"] = parent_fragment_loc
                self.add_edges("hasScript", f)

        logging.info(f"Successfully added {len(functions)} functions to the graph.")

    def add_invocations(self, invocations):
        logging.info("Adding invocations")

        for invocation in invocations.items():
            self.add_edges("invokes", invocation)

        logging.info(f"Successfully added {len(invocations)} invocations to the graph.")

    def contain_orphan_structures(self, contained_structures):
        counter = 0
        handle_counter = 0

        for structure in self.structures.items():
            structure_key = structure[1].get("fullLoc")
            if structure_key and contained_structures.get(structure_key) is None:
                counter += 1
                _, loc_fragment_parent, _ = m3_utils.parse_rascal_loc(
                    structure[1].get("loc")
                )
                if (
                    loc_fragment_parent and loc_fragment_parent in self.containers_structures_simple_names.keys()
                ):
                    parents_full_locs = self.containers_structures_simple_names.get(loc_fragment_parent).get("fullLocs")

                    for parent_full_loc in parents_full_locs:
                        edge_id = hash(parent_full_loc) + hash(structure_key)
                        source = parent_full_loc
                        target = structure[1].get("fullLoc")
                        properties = {"weight": 1}
                        labels = ["contains"]
                        
                        self.append_edge(edge_id, source, properties, target, labels)

                    handle_counter += 1

        logging.info(f"Handled {handle_counter} out of {counter} orphaned structures")

    def handle_unknown_scripts(self, unknown_scripts):
        counter = 0
        def add_script_node(loc_path, script_loc):
            node_id = script_loc[1].get("fragmentType") + ":" + loc_path
            properties = {
                "loc": loc_path,
                "fragmentType": script_loc[1].get("fragmentType"),
                "simpleName": script_loc[1].get("simpleName"),
            }
            labels = ["function"]
            self.append_node(node_id, properties, labels)

        def add_parent_has_script(loc_path, script_parents):
            for parent_full_Loc in script_parents:

                source = parent_full_Loc
                target = script_loc[1].get("fragmentType") + ":" + loc_path
                edge_id = hash(source + target)
                properties = {"weight": 1}
                labels = ["hasScript"]
                self.append_edge(edge_id, source, properties, target, labels)

        logging.info("Adding unknown scripts")
        for script_loc in unknown_scripts.items():
            loc_path, parent_simple_name, _ = m3_utils.parse_rascal_loc(
                script_loc[1].get("loc")
            )
            if (
                parent_simple_name
                and parent_simple_name not in self.containers_structures_simple_names.keys()
            ):
                logging.info(
                    "Missing fragment parent %s not in structures: %s",
                    parent_simple_name,
                    loc_path,
                )
            elif parent_simple_name:
                    add_script_node(loc_path, script_loc)
                    script_parents = self.containers_structures_simple_names.get(
                        parent_simple_name
                    ).get("fullLocs")
                    add_parent_has_script(loc_path, script_parents)
                    counter += 1

        logging.info(f"Added {counter} unknown scripts to the graph")


    def export(self):
        #containers
        namespaces_dict = {}
        #structures
        expanded_macros_dict = {}
        classes_dict = {}
        deferred_classes_dict = {}
        templates_dict = {}
        template_types_dict = {}
        specializations_dict = {}
        partial_specializations_dict = {}
        #operations
        methods_dict = {}
        functions_dict = {}

        def extract_containers():
            nonlocal namespaces_dict
            namespaces_dict = containment_dict.get(constants.M3_CPP_NAMESPACE_TYPE)
            
            self.containers = deepcopy(namespaces_dict)

        def extract_structures():
            self.containers_structures_simple_names = deepcopy(containment_dict.get("containers_structures_simple_names"))

            nonlocal templates_dict, template_types_dict, specializations_dict, partial_specializations_dict, classes_dict, deferred_classes_dict, expanded_macros_dict
            
            expanded_macros_dict = m3_utils.parse_M3_macro_expansions(self.parsed)

            templates_dict = containment_dict.get(constants.M3_CPP_CLASS_TEMPLATE_TYPE)
            template_types_dict = containment_dict.get(constants.M3_TEMPLATE_TYPE_PARAMETER_TYPE)
            specializations_dict = containment_dict.get(constants.M3_CPP_CLASS_SPECIALIZATION_TYPE)
            partial_specializations_dict = containment_dict.get(constants.M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE)
            classes_dict = containment_dict.get(constants.M3_CPP_CLASS_TYPE)
            deferred_classes_dict = containment_dict.get(constants.M3_CPP_DEFERRED_CLASS_TYPE)
                    
            self.structures = deepcopy(templates_dict)
            self.structures.update(template_types_dict)
            self.structures.update(specializations_dict)
            self.structures.update(partial_specializations_dict)
            self.structures.update(classes_dict)
            self.structures.update(deferred_classes_dict)

        def add_containers():
            self.add_namespaces(namespaces_dict)

        def add_structures():
            self.add_macros(expanded_macros_dict)
            self.add_templates(templates_dict)
            self.add_template_types(template_types_dict)
            self.add_specializations(specializations_dict)
            self.add_partial_specializations(partial_specializations_dict)
            self.add_classes(classes_dict)
            self.add_deferred_classes(deferred_classes_dict)

        def extract_scripts():
            nonlocal functions_dict, methods_dict

            functions_dict = containment_dict.get(constants.M3_CPP_FUNCTION_TYPE)
            functions_dict.update(declaredType_dicts.get("functions"))

            methods_dict = declaredType_dicts.get("methods")
            # update method parents from declarations
            declarations_dict = m3_utils.parse_M3_declarations(self.parsed, methods_dict, constants.M3_CPP_METHOD_TYPE)
            methods_dict = declarations_dict.get("fragments")

            self.scripts = deepcopy(methods_dict)
            self.scripts.update(functions_dict)

        def add_scripts():
            self.add_methods(methods_dict)
            self.add_functions(functions_dict)

        # Parse M3 Sections
        declaredType_dicts = m3_utils.parse_M3_declaredType(self.parsed)
        containment_dict, contained_structures = m3_utils.parse_M3_containment(self.parsed)

        # Extract and add nodes to graph:
        extract_containers()
        extract_structures()
        extract_scripts()

        add_containers()
        add_structures()
        add_scripts()

        self.contain_orphan_structures(contained_structures)

        #Extract and add edges to graph
        callGraph_dicts = m3_utils.parse_M3_callGraph(self.parsed, self.scripts)

        invocations = callGraph_dicts.get("invocations")
        # overrides = callGraph_dicts.get("overrides")
        unknown_scripts = callGraph_dicts.get("unknown_scripts")
        # print(self.scripts)
        self.handle_unknown_scripts(unknown_scripts)

        self.add_invocations(invocations)

        with open(self.path, "w") as graph_file:
            graph_file.write(json.dumps(self.lpg))
