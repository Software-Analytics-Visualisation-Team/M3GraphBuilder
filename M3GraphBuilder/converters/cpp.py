from copy import deepcopy
import re
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

    def get_functions(self):
        functions = {}
        problem_declarations = {}
        data = self.parsed["declaredType"]
        for element in data:
            if self.is_rascal_problem(element[0]):
                problem = self.parse_problem(element[0])
                problem_declarations[problem["id"]] = problem
            if re.match("cpp\\+function:", element[0]):
                parameters = []
                function = dict()
                function["functionName"] = re.split(
                    "\\(", re.sub("cpp\\+function:.+\\/", "", element[0])
                )[0]
                #####
                # function["location"] = self.get_function_location(
                #     function["functionName"]
                # )
                #####
                returnField = self.get_type_field(element[1]["returnType"])
                function["returnType"] = self.get_type(
                    element[1]["returnType"], returnField
                )

                if element[1]["parameterTypes"]:
                    if "file" in function["location"].keys():
                        loc = function["location"].get("file")
                    else:
                        loc = None

                    parameters = self.get_parameters(function["functionName"], loc)
                    i = 0
                    for parameter in element[1]["parameterTypes"]:
                        try:
                            parameters[i]["type"] = self.get_parameter_type(
                                parameter, self.get_type_field(parameter)
                            )
                            i += 1
                        except IndexError:
                            pass
                function["parameters"] = parameters
                function["variables"] = self.get_variables(element[0])
                functions[function["functionName"]] = function
        return functions, problem_declarations

    # def get_variables(self, operator):
    #     variables = []
    #     data = self.parsed["declaredType"]
    #     operator_name = "cpp+variable:" + re.split("cpp\\+.+:", operator)[1]
    #     for element in data:
    #         if re.match("cpp\\+variable:", element[0]) and operator_name in element[0]:
    #             variable = {}
    #             variable["name"] = re.sub("cpp\\+variable:.+/", "", element[0])
    #             variable["type"] = self.get_type(
    #                 element[1], self.get_type_field(element[1])
    #             )
    #             variables.append(variable)
    #     return variables

    # def get_methods(self):
    #     data = self.parsed["declaredType"]
    #     methods = {}
    #     for element in data:
    #         parameters = []

    #         if re.match("cpp\\+method", element[0]):
    #             method = dict()
    #             # Addition
    #             elementParts = re.split(
    #                 "\\/", re.sub("cpp\\+method:\\/\\/\\/", "", element[0])
    #             )
    #             # method["class"] = "/".join(elementParts[:-1])
    #             # method["class"] = elementParts[len(elementParts) - 2]

    #             method["methodName"] = re.split(
    #                 "\\(", elementParts[len(elementParts) - 1]
    #             )[0]
    #             # End Addition
    #             # #####
    #             # method["location"] = self.get_method_location(
    #             #     method["class"], method["methodName"]
    #             # )
    #             #####

    #             method["returnType"] = self.get_type(
    #                 element[1]["returnType"],
    #                 self.get_type_field(element[1]["returnType"]),
    #             )

    #             # Addition of second if statement
    #             # if element[1]["parameterTypes"]:
    #             #     if "file" in method["location"].keys():
    #             #         parameters = self.get_parameters(
    #             #             method["methodName"],
    #             #             method["location"].get("file"),
    #             #             method["class"],
    #             #         )
    #             #     else:
    #             #         parameters = self.get_parameters(
    #             #             method["methodName"], "none", method["class"]
    #             #         )

    #             #     i = 0
    #             #     # Addition
    #             #     if len(parameters) != 0:
    #             #         for parameter in element[1]["parameterTypes"]:
    #             #             if i < len(parameters):
    #             #                 parameters[i]["type"] = self.get_parameter_type(
    #             #                     parameter, self.get_type_field(parameter)
    #             #                 )
    #             #                 i += 1

    #             method["parameters"] = {}  # TODO: Attach parameters
    #             method["variables"] = self.get_variables(element[0])
    #             id = method["class"] + "." + method["methodName"]
    #             methods[id] = method
    #     return methods

    # def get_type_field(self, element):
    #     try:
    #         if "baseType" in element.keys():
    #             return "baseType"
    #         if "decl" in element.keys():
    #             return "decl"
    #         if "type" in element.keys():
    #             return "type"
    #         if "msg" in element.keys():
    #             return "msg"
    #         if "templateArguments" in element.keys():
    #             return None
    #     except:
    #         return None

    # def get_type(self, element, field):
    #     if self.get_type_field(element.get(field)) is not None:
    #         return self.get_type(element[field], self.get_type_field(element[field]))
    #     else:
    #         if field == "baseType":
    #             return element[field]
    #         if field == "decl":
    #             if re.match("cpp\\+classTemplate", element[field]):
    #                 return "string"
    #             else:
    #                 elementParts = re.split(
    #                     "\\/", re.sub("cpp\\+class:\\/\\/\\/", "", element[field])
    #                 )
    #                 return elementParts[len(elementParts) - 1]
    #         if field == "msg":
    #             return None

    # def get_parameters(self, function, location, class_name=None):
    #     data = self.parsed["declarations"]
    #     parameters = []

    #     if location is None:
    #         location = ""
    #     if class_name is not None:
    #         find = "" + class_name + "/" + function
    #     else:
    #         find = function

    #     for element in data:
    #         if (
    #             re.match("cpp\\+parameter", element[0])
    #             and find in element[0]
    #             and location in element[1]
    #             and re.match("\\|file:\\/+.+.\\|", element[1])
    #         ):
    #             parameter = {}
    #             parameter["name"] = re.sub("cpp\\+parameter:\\/+.+\\/", "", element[0])
    #             parameter["location"] = int(
    #                 re.split(",", re.sub("\\|file:\\/+.+\\|\\(", "", element[1]))[0]
    #             )
    #             parameters.append(parameter)
    #     parameters = sorted(parameters, key=lambda d: d["location"])
    #     return parameters

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

        function_Definitions_dict = m3_utils.parse_M3_function_Definitions(
            self.parsed, classes
        )  # get class locations

        classes = function_Definitions_dict.get("fragments")
        unlocated_classes = function_Definitions_dict.get("unlocated_fragments")
        files_in_function_Definitions = function_Definitions_dict.get("files")

        if self.verbose:
            print(
                f"[VERBOSE] Succesfully found the physical locations for {len(classes)} classes in 'functionDefinitions'."
            )
            print(
                f"[VERBOSE] Did not find the physical locations of {len(unlocated_classes)} classes in 'functionDefinitions'."
            )

        if len(unlocated_classes) > 0:
            print(
                f"[VERBOSE] Searching for physical locations of unlocated classes in 'declarations'."
            )

            declarations_dict = m3_utils.parse_M3_declarations(
                self.parsed, unlocated_classes
            )
            located_classes = declarations_dict.get("fragments")
            still_unlocated_classes = declarations_dict.get("unlocated_fragments")
            files_in_declarations = declarations_dict.get("files")

        if self.verbose:
            if len(still_unlocated_classes) > 0:
                print(
                    f"[VERBOSE] Succesfully found the physical locations for {len(located_classes)} classes in 'declarations'."
                )
                print(
                    f"[VERBOSE] Did not find the physical locations of {len(still_unlocated_classes)} classes in 'declarations'."
                )
            else:
                print(
                    f"[VERBOSE] Succesfully found the physical locations of all unlocated classes in 'declarations'."
                )

        classes = classes | located_classes

        files_for_classes = set()
        if len(files_in_function_Definitions) > 0:
            files_for_classes.update(files_in_function_Definitions)
        if len(files_in_declarations) > 0:
            files_for_classes.update(files_in_declarations)

        classes = m3_utils.parse_M3_extends(
            self.parsed, classes
        )  # get class extentions
        for c in classes.items():
            class_names.add(c[0])

            self.add_nodes("class", c)
            if c[1].get("extends") is not None:
                self.add_edges("specializes", c)
            self.add_edges("contains", c)

        print(f"Successfully added {len(classes)} classes to the graph.")

        result = {
            "class_names_set": class_names,
            "files_for_classes_set": files_for_classes,
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

        function_Definitions_dict = m3_utils.parse_M3_function_Definitions(
            self.parsed, methods
        )  # get method locations
        methods = function_Definitions_dict.get("fragments")
        unlocated_methods = function_Definitions_dict.get("unlocated_fragments")
        files_in_function_Definitions = function_Definitions_dict.get("files")

        if self.verbose:
            print(
                f"[VERBOSE] Succesfully found the physical locations for {len(methods)} methods in 'functionDefinitions'."
            )
            print(
                f"[VERBOSE] Did not find the physical locations of {len(unlocated_methods)} methods in 'functionDefinitions'."
            )

        if len(unlocated_methods) > 0:
            print(
                f"[VERBOSE] Searching for physical locations of unlocated methods in 'declarations'."
            )

            declarations_dict = m3_utils.parse_M3_declarations(
                self.parsed, unlocated_methods
            )
            located_methods = declarations_dict.get("fragments")
            still_unlocated_methods = declarations_dict.get("unlocated_fragments")
            files_in_declarations = declarations_dict.get("files")

        if self.verbose:
            if len(still_unlocated_methods) > 0:
                print(
                    f"[VERBOSE] Succesfully found the physical locations for {len(located_methods)} methods in 'declarations'."
                )
                print(
                    f"[VERBOSE] Did not find the physical locations of {len(still_unlocated_methods)} methods in 'declarations'."
                )
            else:
                print(
                    f"[VERBOSE] Succesfully found the physical locations of all unlocated methods in 'declarations'."
                )

        methods = methods | located_methods

        files_for_methods = set()
        if len(files_in_function_Definitions) > 0:
            files_for_methods.update(files_in_function_Definitions)
        if len(files_in_declarations) > 0:
            files_for_methods.update(files_in_declarations)

        for m in methods.items():
            self.add_nodes("method", m)

            if m[1].get("class") in class_simple_names:
                self.add_edges("hasScript", m)

            self.add_edges("returnType", m)
            self.add_edges("contains", m)

            method_parameters = parameters.get(m[1].get("functionLoc"))
            if method_parameters is not None:
                print(f"adding params for {m[0]}")
                for param in method_parameters:
                    self.add_nodes("parameter", param)
                    self.add_edges("hasParameter", param)
            else:
                print(f"method {m} with empty parameters")
        # methods = self.get_methods()
        # for m in methods.items():
        #     self.add_nodes("method", m)
        #     self.add_edges("hasScript", m)
        #     # self.add_edges("returnType", m)
        #     # if m[1]["parameters"]:
        #     #     self.add_nodes("parameter", m)
        #     #     self.add_edges("hasParameter", m)
        #     # if m[1]["variables"]:
        #     #     self.add_nodes("variable", m)
        #     #     self.add_edges("hasVariable", m)
        print(f"Successfully added {len(methods)} methods to the graph.")

        result = {"files_for_methods_set": files_for_methods}

        return result

    def add_functions(self, functions, parameters):
        print("Adding functions")

        function_Definitions_dict = m3_utils.parse_M3_function_Definitions(
            self.parsed, functions
        )  # get method locations
        functions_updated_from_Definitions = function_Definitions_dict.get("fragments")
        unlocated_functions = function_Definitions_dict.get("unlocated_fragments")
        files_in_function_Definitions = function_Definitions_dict.get("files")

        if self.verbose:
            print(
                f"[VERBOSE] Succesfully found the physical locations for {len(functions_updated_from_Definitions) - len(unlocated_functions)} functions in 'functionDefinitions'."
            )
            print(
                f"[VERBOSE] Did not find the physical locations of {len(unlocated_functions)} functions in 'functionDefinitions'."
            )

        if len(unlocated_functions) > 0:
            print(
                f"[VERBOSE] Searching for physical locations of unlocated functions in 'declarations'."
            )

            declarations_dict = m3_utils.parse_M3_declarations(
                self.parsed, unlocated_functions
            )
            functions_updated_from_Declarations = declarations_dict.get("fragments")
            still_unlocated_functions = declarations_dict.get("unlocated_fragments")
            files_in_declarations = declarations_dict.get("files")

        if self.verbose:
            if len(still_unlocated_functions) > 0:
                print(
                    f"[VERBOSE] Succesfully found the physical locations for {len(functions_updated_from_Declarations) - len(still_unlocated_functions)} functions in 'declarations'."
                )
                print(
                    f"[VERBOSE] Did not find the physical locations of {len(still_unlocated_functions)} functions in 'declarations'."
                )
            else:
                print(
                    f"[VERBOSE] Succesfully found the physical locations of all unlocated functions in 'declarations'."
                )

        functions_updated = (
            functions_updated_from_Definitions | functions_updated_from_Declarations
        )

        files_for_functions = set()
        if len(files_in_function_Definitions) > 0:
            files_for_functions.update(files_in_function_Definitions)
        if len(files_in_declarations) > 0:
            files_for_functions.update(files_in_declarations)

        for f in functions_updated.items():
            self.add_nodes("function", f)
            self.add_edges("contains", f)
            function_parameters = parameters.get(f[1].get("functionLoc"))
            if function_parameters is not None:
                print(f"adding params for {f[0]}")
                for param in function_parameters:
                    self.add_nodes("parameter", param)
                    self.add_edges("hasParameter", param)
            else:
                print(f"function {f} with empty parameters")

        print(f"Successfully added {len(functions)} functions to the graph.")

        result = {"files_for_functions_set": files_for_functions}

        return result

    def get_invokes(self, operations):
        data = self.parsed["callGraph"]
        invokes = []
        for operation in operations.items():
            for element in data:
                if re.match(".+\\.", operation[0]):
                    source = operation[0].replace(".", "/")
                else:
                    source = operation[0]
                if len(element) > 1:
                    if source in element[0]:
                        invoke = {}
                        invoke["source"] = operation[0]
                        try:
                            target = re.sub("cpp\\+function:\\/+.+\\/", "", element[1])
                            if re.match("cpp\\+", target):
                                target = re.sub("cpp\\+method:\\/+", "", element[1])
                                target = target.replace("/", ".")
                            target = re.split("\\(", target)[0]

                            if target in operations.keys():
                                invoke["target"] = target
                                invokes.append(invoke)
                        except:
                            pass
                    else:
                        pass
        return invokes

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

        # print("Adding declarations")
        # functions, problem_declarations = self.get_functions()
        # for primitve in self.primitives:
        #     self.add_nodes("Primitive", primitve)
        # for problem in problem_declarations.items():
        #     self.add_nodes("problem", problem)
        # print(f"Successfully added {len(problem_declarations)} Rascal problem declarations to the graph.")

        # for func in functions.items():
        #     self.add_nodes("function", func)
        #     # if func[1]["parameters"]:
        #     #     self.add_nodes("parameter", func)
        #     #     self.add_edges("hasParameter", func)
        #     # if func[1]["variables"]:
        #     #     self.add_nodes("variable", func)
        #     #     self.add_edges("hasVariable", func)
        #     # self.add_edges("returnType", func)
        #     self.add_edges("contains", func)
        # print(f"Successfully added {len(functions)} functions to the graph.")

        add_classes_dict = self.add_classes(
            containment_dict.get("classes")
        )  # collect classes for method location
        class_names = add_classes_dict.get("class_names_set")
        files_for_classes = add_classes_dict.get("files_for_classes_set")

        # print("Adding Rascal problem classes")
        # for pc in problem_classes.items():
        #     self.add_nodes("problem", pc)
        # print(
        #     f"Successfully added {len(problem_classes)} Rascal problem classes to the graph."
        # )

        declaredType_dicts = m3_utils.parse_M3_declaredType(self.parsed)
        declarations_dict = m3_utils.parse_M3_declarations(self.parsed)

        add_methods_dict = self.add_methods(
            declaredType_dicts.get("methods"),
            class_names,
            declarations_dict.get("parameters"),
        )
        files_for_methods = add_methods_dict.get("files_for_methods_set")

        # print(declarations_dict.get("parameters"))

        add_functions_dict = self.add_functions(
            declaredType_dicts.get("functions"), declarations_dict.get("parameters")
        )
        files_for_functions = add_functions_dict.get("files_for_functions_set")

        files_set = m3_utils.parse_M3_provides(self.parsed)
        files_set.update(files_for_classes)
        files_set.update(files_for_methods)
        files_set.update(files_for_functions)

        self.add_files(files_set)

        # print("Adding invokes")
        # operations = deepcopy(methods)
        # operations.update(functions)
        # for invoke in self.get_invokes(operations):
        #     self.add_edges("invokes", invoke)
        # print(f"Successfully added {len(operations)} invokes to the graph.")

        with open(self.path, "w") as graph_file:
            graph_file.write(json.dumps(self.lpg))
