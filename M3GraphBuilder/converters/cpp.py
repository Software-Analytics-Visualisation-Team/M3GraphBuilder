from copy import deepcopy
import json
import M3GraphBuilder.converters.constants as constants
import M3GraphBuilder.converters.m3_utils as m3_utils
import M3GraphBuilder.logging_utils as logging


logger = logging.setup_logger("cpp_logger", "cpp_logfile.log")


class Cpp:
    primitives = ["int", "double", "float", "void", "char", "string", "boolean"]
    lpg = {"elements": {"nodes": [], "edges": []}}
    parsed = None
    path = None
    containers = {}
    structures = {}
    operations = {}

    def __init__(self, path, parsed, verbose, issues=None) -> None:
        self.path = path
        self.parsed = parsed
        self.verbose = verbose
        self.issues = issues

    def add_edges(self, kind, content):
        edge_id = {}
        source = {}
        properties = {}
        target = {}
        labels = []

        match kind:
            case "hasScript":
                edge_id = hash(content[0])
                source = content[1].get("parent")
                properties = {"weight": 1}
                target = content[1].get("loc")
                labels = [kind]

            case "hasParameter":
                edge_id = hash(content[1].get("simpleName"))
                source = content[1].get("function")
                properties = {"weight": 1}
                target = (
                    content[1].get("functionLoc") + "." + content[1].get("simpleName")
                )
                labels = [kind]

            case "returnType":
                edge_id = hash(content[0]) + hash(content[1]["returnType"])
                source = content[0]
                properties = {"weight": 1}
                target = content[1]["returnType"]
                labels = [kind]

            case "specializes":
                for base_fragment in content[1]["extends"]:
                    edge_id = hash(content[0]) + hash(base_fragment)
                    self.lpg["elements"]["edges"].append(
                        {
                            "data": {
                                "id": edge_id,
                                "source": base_fragment,
                                "properties": {"weight": 1},
                                "target": content[1].get("loc"),
                                "labels": [kind],
                            }
                        }
                    )

            case "hasVariable":
                for variable in content[1]["variables"]:
                    if variable is not None and variable != "":
                        edge_id = hash(variable["name"]) + hash(content[0])
                        self.lpg["elements"]["edges"].append(
                            {
                                "data": {
                                    "id": edge_id,
                                    "source": content[0],
                                    "properties": {"weight": 1},
                                    "target": content[0] + "." + variable["name"],
                                    "labels": [kind],
                                }
                            }
                        )
                        if len(content[1]["location"]) != 0 and content[0] is not None:
                            edge_id = (
                                hash(variable["name"])
                                + hash(content[0])
                                + hash(content[1]["location"].get("file"))
                            )
                            self.lpg["elements"]["edges"].append(
                                {
                                    "data": {
                                        "id": edge_id,
                                        "source": content[1]["location"].get("file"),
                                        "properties": {"weight": 1},
                                        "target": content[0] + "." + variable["name"],
                                        "labels": ["contains"],
                                    }
                                }
                            )

            case "invokes":
                edge_id = hash(content[1].get("id"))
                self.lpg["elements"]["edges"].append(
                    {
                        "data": {
                            "id": edge_id,
                            "source": content[1]["source"],
                            "properties": {"weight": content[1]["weight"]},
                            "target": content[1]["target"],
                            "labels": [kind],
                        }
                    }
                )

            case "contains":
                try:
                    # Namespace and translation unit relationships
                    if (
                        content[1].get("fragmentType")
                        is constants.M3_CPP_TRANSLATION_UNIT_TYPE
                        or content[1].get("fragmentType")
                        is constants.M3_CPP_NAMESPACE_TYPE
                    ):
                        contained_fragments = content[1].get("contains")
                        if contained_fragments is not None:

                            for child_fragment in contained_fragments:
                                edge_id = hash(content[0]) + hash(child_fragment)

                                self.lpg["elements"]["edges"].append(
                                    {
                                        "data": {
                                            "id": edge_id,
                                            "source": content[1].get("loc"),
                                            "properties": {"weight": 1},
                                            "target": child_fragment,
                                            "labels": [kind],
                                        }
                                    }
                                )
                    # Method relationships
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
                            properties = {"weight": 1}
                            target = content[0]
                            labels = ["contains"]
                        except:
                            logger.info(
                                f"Failed adding contains relationship between {source} and {target}"
                            )
                            logger.info("Trying backup.")
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
                                properties = {"weight": 1}
                                target = content[0]
                                labels = ["contains"]
                            else:
                                logger.info(
                                    f"Failed to add a contains edge for {content}"
                                )
                                return
                    # Classes relationships
                    elif content[1].get("location") is not None:
                        edge_id = hash(content[0]) + hash(
                            content[1]["location"]["file"]
                        )
                        source = content[1]["location"].get("file")
                        properties = {"weight": 1}
                        target = content[0]
                        labels = ["contains"]
                except Exception as e:
                    logger.info("Problem adding 'contains' relationship for ", content)

            case "type":
                content = list(zip(content.keys(), content.values()))[0]
                id = hash(content[0]) - hash(content[1]["name"])
                if len(content[1]["type"]) != 0:

                    self.lpg["elements"]["edges"].append(
                        {
                            "data": {
                                "id": id,
                                "source": content[0] + "." + content[1]["name"],
                                "properties": {"weight": 1},
                                "target": content[1]["type"],
                                "labels": [kind],
                            }
                        }
                    )

        if edge_id and source and properties and target and labels:
            self.append_edge(edge_id, source, properties, target, labels)

    def append_node(self, node_id, properties, labels):
        try:
            self.lpg["elements"]["nodes"].append(
                {"data": {"id": node_id, "properties": properties, "labels": labels}}
            )
        except Exception as e:
            logger.info(f"Problem adding {labels} node relationship for ", node_id)
            logger.info(e)

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
            logger.info(f"Problem adding edge with id: {edge_id} to the graph")
            logger.info(e)

    def add_nodes(self, kind, content):
        node_id = {}
        properties = {}
        labels = []
        location = (
            content[1]["physicalLoc"]["file"]
            if content[1].get("physicalLoc") is not None
            else content[1]["loc"]
        )

        match kind:
            case "problem":
                node_id = content[1]["id"]
                properties = {
                    "simpleName": content[1]["id"],
                    "description": content[1]["message"],
                    "kind": kind,
                }
                labels = [["Problem"]]

            case "translation_unit":
                node_id = content[1].get("loc")
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "description": content[1].get("loc"),
                    "kind": "file",
                }
                labels = [["Container"]]

            case "file":
                node_id = content
                properties = {"simpleName": content, "kind": kind}
                labels = ["Container"]

            case "function":
                node_id = content[1].get("loc")
                properties = {
                    "simpleName": content[1]["simpleName"],
                    "description": location,
                    "kind": kind,
                }
                labels = ["Operation"]

            case "parameter":
                node_id = (
                    content[1].get("functionLoc") + "." + content[1].get("simpleName")
                )
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "kind": kind,
                    "description": location,
                }
                labels = ["Variable"]

            case "method":
                node_id = content[1].get("loc")
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
            ):
                node_id = content[1].get("loc")
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "kind": kind,
                    "description": location,
                }
                labels = ["Structure"]

            case "namespace":
                node_id = content[1].get("loc")
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "kind": "package",
                    "description": location,
                }
                labels = ["Container"]

            case "Primitive":
                self.lpg["elements"]["nodes"].append(
                    {
                        "data": {
                            "id": content,
                            "properties": {
                                "simpleName": content,
                                "kind": kind,
                                "description": location,
                            },
                            "labels": [kind],
                        }
                    }
                )

            case "variable":
                for variable in content[1]["variables"]:
                    if variable is not None and variable != "":
                        self.lpg["elements"]["nodes"].append(
                            {
                                "data": {
                                    "id": content[0] + "." + variable["name"],
                                    "properties": {
                                        "simpleName": variable["name"],
                                        "kind": kind,
                                    },
                                    "labels": ["Variable"],
                                }
                            }
                        )
                        if variable["type"] is not None:
                            self.add_edges("type", {content[0]: variable})

        self.append_node(node_id, properties, labels)

    def get_fragment_files(self, fragments):
        function_Definitions_dict = m3_utils.parse_M3_function_Definitions(
            self.parsed, fragments
        )
        fragments_updated_from_Definitions = function_Definitions_dict.get("fragments")
        unlocated_fragments = function_Definitions_dict.get("unlocated_fragments")
        files_in_function_Definitions = function_Definitions_dict.get("files")

        if self.verbose:
            logger.info(
                f"[VERBOSE] Succesfully found the physical locations for {len(fragments_updated_from_Definitions) - len(unlocated_fragments)} fragments in 'functionDefinitions'."
            )
            logger.info(
                f"[VERBOSE] Did not find the physical locations of {len(unlocated_fragments)} fragments in 'functionDefinitions'."
            )

        if len(unlocated_fragments) > 0:
            logger.info(
                f"[VERBOSE] Searching for physical locations of unlocated fragments in 'declarations'."
            )

            declarations_dict = m3_utils.parse_M3_declarations(self.parsed, fragments)
            fragments_updated_from_Declarations = declarations_dict.get("fragments")
            still_unlocated_fragments = declarations_dict.get("unlocated_fragments")
            files_in_declarations = declarations_dict.get("files")

        if self.verbose:
            if len(still_unlocated_fragments) > 0:
                logger.info(
                    f"[VERBOSE] Succesfully found the physical locations for {len(fragments_updated_from_Declarations) - len(still_unlocated_fragments)} fragments in 'declarations'."
                )
                logger.info(
                    f"[VERBOSE] Did not find the physical locations of {len(still_unlocated_fragments)} fragments in 'declarations'."
                )
            else:
                logger.info(
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
        logger.info("Adding namespaces")
        for n in namespaces.items():
            self.add_nodes("namespace", n)
            if n[1].get("contains") is not None:
                self.add_edges("contains", n)

        logger.info(f"Successfully added {len(namespaces)} namespaces to the graph.")

    def add_translation_units(self, translation_units):
        logger.info("Adding translation units")

        for tu in translation_units.items():
            self.add_nodes("translation_unit", tu)
            self.add_edges("contains", tu)

        logger.info(
            f"Successfully added {len(translation_units)} translation units to the graph."
        )

    def add_files(self, files):
        logger.info("Adding files")

        for file in files:
            self.add_nodes("file", file)

        logger.info(f"Successfully added {len(files)} files to the graph.")

    def add_classes(self, classes):
        logger.info("Adding classes")
        # files = []

        if self.verbose:
            logger.info(
                f"[VERBOSE] Updating declared locations for {len(classes)} classes."
            )

        # get_fragment_files_dict = self.get_fragment_files(classes)
        # updated_classes = get_fragment_files_dict.get("fragments")
        # files = get_fragment_files_dict.get("files")

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, classes, constants.M3_CPP_CLASS_TYPE
        )
        classes_updated_from_Declarations = declarations_dict.get("fragments")

        updated_classes_with_extensions = m3_utils.parse_M3_extends(
            self.parsed, classes_updated_from_Declarations, constants.M3_CPP_CLASS_TYPE
        )  # get class extentions
        for c in updated_classes_with_extensions.items():
            self.add_nodes("class", c)
            if c[1].get("extends") is not None:
                self.add_edges("specializes", c)
            # self.add_edges("contains", c)

        logger.info(f"Successfully added {len(classes)} classes to the graph.")

        # result = {
        #     "simplified_class_dict": simplified_class,
        #     "files_for_classes_set": files,
        # }

        # return result

    def add_templates(self, templates):
        logger.info("Adding templates")

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

        logger.info(f"Successfully added {len(templates)} templates to the graph.")

    def add_template_types(self, template_types):
        logger.info("Adding template types")

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, template_types, constants.M3_TEMPLATE_TYPE_PARAM_LOC_SCM
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

        logger.info(
            f"Successfully added {len(template_types)} template types to the graph."
        )

    def add_specializations(self, specializations):
        logger.info("Adding specializations")

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

        logger.info(
            f"Successfully added {len(specializations)} specializations to the graph."
        )

    def add_partial_specializations(self, partial_specializations):
        logger.info("Adding partial specializations")

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

        logger.info(
            f"Successfully added {len(partial_specializations)} partial specializations to the graph."
        )

    def add_methods(self, methods, parameters):
        logger.info("Adding methods")

        if self.verbose:
            logger.info(
                f"[VERBOSE] Updating declared locations for {len(methods)} methods."
            )

        # get_fragment_files_dict = self.get_fragment_files(methods)
        # updated_methods = get_fragment_files_dict.get("fragments")
        # files_for_methods = get_fragment_files_dict.get("files")

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, methods, constants.M3_CPP_METHOD_TYPE
        )
        methods_updated_from_Declarations = declarations_dict.get("fragments")

        for m in methods_updated_from_Declarations.items():
            self.add_nodes("method", m)
            # logger.debug("method parent %s", m[1].get("parent"))
            if m[1].get("parent") in self.structures.keys():
                # logger.debug("parent successfully recognized")
                parent_fragment = self.structures.get(m[1]["parent"])

                m[1]["parent"] = parent_fragment.get("loc")
                self.add_edges("hasScript", m)

            # self.add_edges("returnType", m)
            # self.add_edges("contains", m)

            method_parameters = parameters.get(m[1].get("functionLoc"))
            if method_parameters is not None:
                # logger.info(f"adding params for {m[0]}")
                for param in method_parameters:
                    self.add_nodes("parameter", param)
                    self.add_edges("hasParameter", param)
            # else:
            #     logger.info(f"method {m} with empty parameters")

        logger.info(f"Successfully added {len(methods)} methods to the graph.")

        # result = {"files_for_methods_set": files_for_methods}

        # return result

    def add_functions(self, functions, containers_dict, parameters):
        logger.info("Adding functions")

        if self.verbose:
            logger.info(
                f"[VERBOSE] Updating declared locations for {len(functions)} functions."
            )

        # get_fragment_files_dict = self.get_fragment_files(functions)
        # updated_functions = get_fragment_files_dict.get("fragments")
        # files_for_functions = get_fragment_files_dict.get("files")

        declarations_dict = m3_utils.parse_M3_declarations(
            self.parsed, functions, constants.M3_CPP_FUNCTION_TYPE
        )
        functions_updated_from_Declarations = declarations_dict.get("fragments")

        for f in functions_updated_from_Declarations.items():
            self.add_nodes("function", f)

            if f[1].get("parent") in containers_dict.keys():
                # logger.debug("parent successfully recognized")
                parent_fragment = containers_dict.get(f[1]["parent"])

                f[1]["parent"] = parent_fragment.get("loc")
                self.add_edges("hasScript", f)

            # self.add_edges("contains", f)
            function_parameters = parameters.get(f[1].get("functionLoc"))

            if function_parameters is not None:
                for param in function_parameters:
                    self.add_nodes("parameter", param)
                    self.add_edges("hasParameter", param)
            else:
                logger.debug("function %s with empty parameters", f)

        logger.info(f"Successfully added {len(functions)} functions to the graph.")

        # result = {"files_for_functions_set": files_for_functions}

        # return result

    def add_invocations(self, methods, functions):
        logger.info("Adding invocations")

        self.operations = deepcopy(methods)
        self.operations.update(functions)
        callGraph_data = m3_utils.parse_M3_callGraph(self.parsed, self.operations)
        invocations = callGraph_data.get("invocations")
        for invocation in invocations.items():
            self.add_edges("invokes", invocation)

        logger.info(f"Successfully added {len(invocations)} invocations to the graph.")

    def export(self):
        containment_dict = m3_utils.parse_M3_containment(self.parsed)

        namespaces_dict = containment_dict.get(constants.M3_CPP_NAMESPACE_TYPE)
        self.add_namespaces(namespaces_dict)
        self.containers = deepcopy(namespaces_dict)

        # self.add_translation_units(containment_dict.get(constants.M3_CPP_TRANSLATION_UNIT_TYPE))

        templates_dict = containment_dict.get(constants.M3_CPP_CLASS_TEMPLATE_TYPE)
        self.add_templates(templates_dict)
        self.structures = deepcopy(templates_dict)

        template_types_dict = containment_dict.get(
            constants.M3_TEMPLATE_TYPE_PARAMETER_TYPE
        )
        self.add_template_types(template_types_dict)

        specializations_dict = containment_dict.get(
            constants.M3_CPP_CLASS_SPECIALIZATION_TYPE
        )
        self.add_specializations(specializations_dict)
        self.structures.update(specializations_dict)

        partial_specializations_dict = containment_dict.get(
            constants.M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE
        )
        self.add_partial_specializations(partial_specializations_dict)
        self.structures.update(specializations_dict)

        classes_dict = containment_dict.get(constants.M3_CPP_CLASS_TYPE)
        self.add_classes(classes_dict)
        self.structures.update(classes_dict)

        # files_for_classes = add_classes_dict.get("files_for_classes_set")

        declaredType_dicts = m3_utils.parse_M3_declaredType(self.parsed)
        declarations_dict = m3_utils.parse_M3_declarations(self.parsed)

        add_methods_dict = self.add_methods(
            declaredType_dicts.get("methods"),
            declarations_dict.get("parameters"),
        )
        # files_for_methods = add_methods_dict.get("files_for_methods_set")

        self.add_functions(
            declaredType_dicts.get("functions"),
            namespaces_dict,
            declarations_dict.get("parameters"),
        )
        # files_for_functions = add_functions_dict.get("files_for_functions_set")

        self.add_invocations(
            declaredType_dicts.get("methods"), declaredType_dicts.get("functions")
        )

        # files_set = m3_utils.parse_M3_provides(self.parsed)
        # files_set.update(files_for_classes)
        # files_set.update(files_for_methods)
        # files_set.update(files_for_functions)

        # self.add_files(files_set)

        with open(self.path, "w") as graph_file:
            graph_file.write(json.dumps(self.lpg))
