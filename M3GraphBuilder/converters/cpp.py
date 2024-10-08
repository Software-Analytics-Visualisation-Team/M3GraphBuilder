from copy import deepcopy
import json
import M3GraphBuilder.converters.constants as constants
import M3GraphBuilder.converters.m3_utils as m3_utils


class Cpp:
    primitives = ["int", "double", "float", "void", "char", "string", "boolean"]
    lpg = {"elements": {"nodes": [], "edges": []}}
    parsed = None
    path = None

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
                source = content[1].get("class")
                properties = {"weight": 1}
                target = content[0]
                labels = [kind]

            case "hasParameter":
                edge_id = hash(content[1].get("simpleName"))
                source = content[1].get("function")
                properties = {"weight": 1}
                target = (
                    content[1].get("functionLoc") + "." + content[1].get("simpleName")
                )
                labels = [kind]

                # for parameter in content[1]["parameters"]:
                #     if parameter is not None and parameter != "":
                #         edge_id = hash(parameter["name"]) + hash(content[0])
                #         self.lpg["elements"]["edges"].append(
                #             {
                #                 "data": {
                #                     "id": edge_id,
                #                     "source": content[0],
                #                     "properties": {"weight": 1},
                #                     "target": content[0] + "." + parameter["name"],
                #                     "labels": [kind],
                #                 }
                #             }
                #         )

                # if len(content[1]["location"]) != 0:
                #     edge_id = (
                #         hash(parameter["name"])
                #         + hash(content[0])
                #         + hash(content[1]["location"].get("file"))
                #     )
                #     self.lpg["elements"]["edges"].append(
                #         {
                #             "data": {
                #                 "id": edge_id,
                #                 "source": content[1]["location"].get("file"),
                #                 "properties": {"weight": 1},
                #                 "target": content[0] + "." + parameter["name"],
                #                 "labels": ["contains"],
                #             }
                #         }
                #     )

            case "returnType":
                # if content[0] is not None and content[1]["returnType"] is not None:
                edge_id = hash(content[0]) + hash(content[1]["returnType"])
                source = content[0]
                properties = {"weight": 1}
                target = content[1]["returnType"]
                labels = [kind]

            case "specializes":
                edge_id = hash(content[0]) + hash(content[1]["extends"])
                self.lpg["elements"]["edges"].append(
                    {
                        "data": {
                            "id": edge_id,
                            "source": content[0],
                            "properties": {"weight": 1},
                            "target": content[1]["extends"],
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
                edge_id = hash(content["target"]) + hash(content["source"])
                self.lpg["elements"]["edges"].append(
                    {
                        "data": {
                            "id": edge_id,
                            "source": content["source"],
                            "properties": {"weight": 1},
                            "target": content["target"],
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
                        children_namespaces = content[1].get("contains")
                        if children_namespaces is not None:
                            for child_namespace in children_namespaces:
                                edge_id = hash(content[0]) + hash(child_namespace)
                            self.lpg["elements"]["edges"].append(
                                {
                                    "data": {
                                        "id": edge_id,
                                        "source": content[1].get("simpleName"),
                                        "properties": {"weight": 1},
                                        "target": child_namespace,
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
                            print(
                                f"Failed adding contains relationship between {source} and {target}"
                            )
                            print("Trying backup.")
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
                                print(f"Failed to add a contains edge for {content}")
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
                    print("Problem adding 'contains' relationship for ", content)
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
            print(f"Problem adding {labels} node relationship for ", node_id)
            print(e)

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
            print(f"Problem adding edge with id: {edge_id} to the graph")
            print(e)

    def add_nodes(self, kind, content):
        node_id = {}
        properties = {}
        labels = []

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
                node_id = content[1].get("simpleName")
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
                node_id = content[0]
                properties = {
                    "simpleName": content[1]["simpleName"],
                    "kind": kind,
                    # "vulnerabilities": vulnerabilities,
                    # "location": content[1]["location"],
                }
                labels = [
                    "Operation",
                    # "vulnerable" if len(vulnerabilities) > 0 else "",
                ]
                # vulnerabilities = []
                # if self.issues is not None:
                #     for issue in self.issues:
                #         if issue["target"]["script"] == content[0]:
                #             vulnerabilities.append(issue)

            case "parameter":
                node_id = (
                    content[1].get("functionLoc") + "." + content[1].get("simpleName")
                )
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "kind": kind,
                }
                labels = ["Variable"]

                # for parameter in content[1]["parameters"]:
                #     if parameter is not None and parameter != "":
                #         self.lpg["elements"]["nodes"].append(
                #             {
                #                 "data": {
                #                     "id": content[0] + "." + parameter["name"],
                #                     "properties": {
                #                         "simpleName": parameter["name"],
                #                         "kind": kind,
                #                     },
                #                     "labels": ["Variable"],
                #                 }
                #             }
                #         )
                #         if "type" in parameter.keys() and parameter["type"] is not None:
                #             self.add_edges("type", {content[0]: parameter})
            case "method":
                # vulnerabilities = []
                # if self.issues is not None:
                #     for issue in self.issues:
                #         if issue["target"]["script"] == content[0]:
                #             vulnerabilities.append(issue)
                # if content[0] != "" and content[1] != "":
                node_id = content[0]
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "kind": kind,
                    "description": content[1].get("loc"),
                    # "vulnerabilities": vulnerabilities,
                }
                labels = ["Operation"]
                # "vulnerable" if len(vulnerabilities) > 0 else "",
                # self.lpg["elements"]["nodes"].append(
                #     {
                #         "data": {
                #             "id": content[0],
                #             "properties": {
                #                 "simpleName": content[1]["methodName"],
                #                 "kind": kind,
                #                 "vulnerabilities": vulnerabilities,
                #             },
                #             "labels": [
                #                 "Operation",
                #                 # "vulnerable" if len(vulnerabilities) > 0 else "",
                #             ],
                #         }
                #     }
                # )
            case (
                "class"
                | "namespace"
                | "template"
                | "template_type"
                | "specialization"
                | "partial_specialization"
            ):
                # print(content)
                # vulnerabilities = []
                # if self.issues is not None:
                #     for issue in self.issues:
                #         if issue["target"]["script"] == content[0]:
                #             vulnerabilities.append(issue)
                node_id = content[1].get("simpleName")
                properties = {
                    "simpleName": content[1].get("simpleName"),
                    "kind": kind,
                    # "vulnerabilities": vulnerabilities,
                    "description": content[1].get("loc"),
                }
                labels = ["Structure"]
                # "vulnerable" if len(vulnerabilities) > 0 else "",

            case "Primitive":
                self.lpg["elements"]["nodes"].append(
                    {
                        "data": {
                            "id": content,
                            "properties": {"simpleName": content, "kind": kind},
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
            print(
                f"[VERBOSE] Succesfully found the physical locations for {len(fragments_updated_from_Definitions) - len(unlocated_fragments)} fragments in 'functionDefinitions'."
            )
            print(
                f"[VERBOSE] Did not find the physical locations of {len(unlocated_fragments)} fragments in 'functionDefinitions'."
            )

        if len(unlocated_fragments) > 0:
            print(
                f"[VERBOSE] Searching for physical locations of unlocated fragments in 'declarations'."
            )

            declarations_dict = m3_utils.parse_M3_declarations(
                self.parsed, unlocated_fragments
            )
            fragments_updated_from_Declarations = declarations_dict.get("fragments")
            still_unlocated_fragments = declarations_dict.get("unlocated_fragments")
            files_in_declarations = declarations_dict.get("files")

        if self.verbose:
            if len(still_unlocated_fragments) > 0:
                print(
                    f"[VERBOSE] Succesfully found the physical locations for {len(fragments_updated_from_Declarations) - len(still_unlocated_fragments)} fragments in 'declarations'."
                )
                print(
                    f"[VERBOSE] Did not find the physical locations of {len(still_unlocated_fragments)} fragments in 'declarations'."
                )
            else:
                print(
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
        print("Adding namespaces")

        for n in namespaces.items():
            self.add_nodes("namespace", n)
            if n[1].get("contains") is not None:
                self.add_edges("contains", n)

        print(f"Successfully added {len(namespaces)} namespaces to the graph.")

    def add_translation_units(self, translation_units):
        print("Adding translation units")

        for tu in translation_units.items():
            self.add_nodes("translation_unit", tu)
            self.add_edges("contains", tu)

        print(
            f"Successfully added {len(translation_units)} translation units to the graph."
        )

    def add_files(self, files):
        print("Adding files")

        for file in files:
            self.add_nodes("file", file)

        print(f"Successfully added {len(files)} files to the graph.")

    def add_classes(self, classes):
        print("Adding classes")
        class_names = set()

        if self.verbose:
            print(f"[VERBOSE] Updating declared locations for {len(classes)} classes.")

        get_fragment_files_dict = self.get_fragment_files(classes)
        updated_classes = get_fragment_files_dict.get("fragments")
        files = get_fragment_files_dict.get("files")

        updated_classes_with_extensions = m3_utils.parse_M3_extends(
            self.parsed, updated_classes
        )  # get class extentions
        for c in updated_classes_with_extensions.items():
            class_names.add(c[0])

            self.add_nodes("class", c)
            if c[1].get("extends") is not None:
                self.add_edges("specializes", c)
            self.add_edges("contains", c)

        print(f"Successfully added {len(classes)} classes to the graph.")

        result = {
            "class_names_set": class_names,
            "files_for_classes_set": files,
        }

        return result

    def add_templates(self, templates):
        print("Adding templates")

        for temp in templates.items():
            self.add_nodes("template", temp)

        print(f"Successfully added {len(templates)} templates to the graph.")

    def add_template_types(self, template_types):
        print("Adding template types")

        for temp_type in template_types.items():
            self.add_nodes("template_type", temp_type)

        print(f"Successfully added {len(template_types)} template types to the graph.")

    def add_specializations(self, specializations):
        print("Adding specializations")

        for spec in specializations.items():
            self.add_nodes("specialization", spec)

        print(
            f"Successfully added {len(specializations)} specializations to the graph."
        )

    def add_partial_specializations(self, partial_specializations):
        print("Adding partial specializations")

        for part_spec in partial_specializations.items():
            self.add_nodes("partial_specialization", part_spec)

        print(
            f"Successfully added {len(partial_specializations)} partial specializations to the graph."
        )

    def add_methods(self, methods, class_simple_names, parameters):
        print("Adding methods")

        if self.verbose:
            print(f"[VERBOSE] Updating declared locations for {len(methods)} methods.")

        get_fragment_files_dict = self.get_fragment_files(methods)
        updated_methods = get_fragment_files_dict.get("fragments")
        files_for_methods = get_fragment_files_dict.get("files")

        for m in updated_methods.items():
            self.add_nodes("method", m)

            if m[1].get("class") in class_simple_names:
                self.add_edges("hasScript", m)

            self.add_edges("returnType", m)
            self.add_edges("contains", m)

            method_parameters = parameters.get(m[1].get("functionLoc"))
            if method_parameters is not None:
                # print(f"adding params for {m[0]}")
                for param in method_parameters:
                    self.add_nodes("parameter", param)
                    self.add_edges("hasParameter", param)
            # else:
            #     print(f"method {m} with empty parameters")

        print(f"Successfully added {len(methods)} methods to the graph.")

        result = {"files_for_methods_set": files_for_methods}

        return result

    def add_functions(self, functions, parameters):
        print("Adding functions")

        if self.verbose:
            print(
                f"[VERBOSE] Updating declared locations for {len(functions)} functions."
            )

        get_fragment_files_dict = self.get_fragment_files(functions)
        updated_functions = get_fragment_files_dict.get("fragments")
        files_for_functions = get_fragment_files_dict.get("files")

        for f in updated_functions.items():
            self.add_nodes("function", f)
            self.add_edges("contains", f)
            function_parameters = parameters.get(f[1].get("functionLoc"))
            if function_parameters is not None:
                # print(f"adding params for {f[0]}")
                for param in function_parameters:
                    self.add_nodes("parameter", param)
                    self.add_edges("hasParameter", param)
            # else:
            #     print(f"function {f} with empty parameters")

        print(f"Successfully added {len(functions)} functions to the graph.")

        result = {"files_for_functions_set": files_for_functions}

        return result

    def add_invocations(self, methods, functions):
        print("Adding invocations")

        operations = deepcopy(methods)
        operations.update(functions)
        invocations = m3_utils.parse_M3_callGraph(self.parsed, operations)
        for invoke in invocations:
            self.add_edges("invokes", invoke)

        print(f"Successfully added {len(invocations)} invocations to the graph.")

    def export(self):
        containment_dict = m3_utils.parse_M3_containment(self.parsed)
        self.add_namespaces(containment_dict.get("namespaces"))
        self.add_translation_units(containment_dict.get("translation_units"))
        self.add_templates(containment_dict.get("templates"))
        self.add_template_types(containment_dict.get("template_types"))
        self.add_specializations(containment_dict.get("specializations"))
        self.add_partial_specializations(
            containment_dict.get("partial_specializations")
        )

        add_classes_dict = self.add_classes(containment_dict.get("classes"))
        class_names = add_classes_dict.get("class_names_set")
        files_for_classes = add_classes_dict.get("files_for_classes_set")

        declaredType_dicts = m3_utils.parse_M3_declaredType(self.parsed)
        declarations_dict = m3_utils.parse_M3_declarations(self.parsed)

        add_methods_dict = self.add_methods(
            declaredType_dicts.get("methods"),
            class_names,
            declarations_dict.get("parameters"),
        )
        files_for_methods = add_methods_dict.get("files_for_methods_set")

        add_functions_dict = self.add_functions(
            declaredType_dicts.get("functions"), declarations_dict.get("parameters")
        )
        files_for_functions = add_functions_dict.get("files_for_functions_set")

        self.add_invocations(
            declaredType_dicts.get("methods"), declaredType_dicts.get("functions")
        )

        files_set = m3_utils.parse_M3_provides(self.parsed)
        files_set.update(files_for_classes)
        files_set.update(files_for_methods)
        files_set.update(files_for_functions)

        self.add_files(files_set)

        with open(self.path, "w") as graph_file:
            graph_file.write(json.dumps(self.lpg))
