import re
from typing import Any, Dict
import M3GraphBuilder.converters.constants as constants
import logging


def parse_M3_function_Definitions(m3, fragments_dict):
    function_Definitions_data = m3["functionDefinitions"]
    unlocated_fragments_dict = {}
    files_containing_fragments_set = set()
    for rel in function_Definitions_data:
        function_Definitions_fragment = parse_M3_loc_statement(rel[0])
        for key in fragments_dict.keys():
            if fragments_dict[key].get(
                "simpleName"
            ) == function_Definitions_fragment.get("simpleName"):
                fragments_dict[key]["location"] = get_fragment_declaration_location(
                    rel[1]
                )

    for fragment in fragments_dict.items():
        location = fragment[1].get("location")
        if location is None:
            unlocated_fragments_dict[fragment[1].get("simpleName")] = fragment[1]
        else:
            files_containing_fragments_set.add(location["file"])

    result = {
        "fragments": fragments_dict,
        "unlocated_fragments": unlocated_fragments_dict,
        "files": files_containing_fragments_set,
    }

    return result


def parse_M3_declarations(m3, fragments_dict=None, fragments_type=None):
    declarations_data = m3["declarations"]
    unlocated_fragments_dict = {}
    parameters_dict = {}
    translation_units_dict = {}
    files_containing_fragments_set = set()
    counter_for_located_fragments = 0

    for rel in declarations_data:
        declarations_fragment = parse_M3_loc_statement(rel[0])

        if fragments_dict is None:
            match declarations_fragment["fragmentType"]:
                case constants.M3_CPP_PARAMETER_TYPE:
                    declarations_fragment = update_parameter_info(
                        declarations_fragment, rel
                    )

                    if declarations_fragment is not None:

                        parameters_for_function = parameters_dict.get(
                            declarations_fragment["functionLoc"]
                        )

                        if parameters_for_function is None:
                            parameters_dict[declarations_fragment["functionLoc"]] = [
                                declarations_fragment
                            ]
                        else:
                            parameters_for_function.append(declarations_fragment)
                            parameters_dict[declarations_fragment["functionLoc"]] = (
                                parameters_for_function
                            )
                case constants.M3_CPP_TRANSLATION_UNIT_TYPE:
                    declarations_fragment["physicalLoc"] = rel[1]
                    translation_units_dict[declarations_fragment.get("loc")] = (
                        declarations_fragment
                    )

        else:
            key = declarations_fragment.get("loc")
            if key is not None and key in fragments_dict.keys():
                fragments_dict[key]["physicalLoc"] = get_fragment_declaration_location(
                    rel[1]
                )
                counter_for_located_fragments = counter_for_located_fragments + 1

    if fragments_dict is not None:
        logging.debug(
            "Located %s fragments out of %s fragments of type %s.",
            counter_for_located_fragments,
            fragments_type,
            len(fragments_dict),
        )

    result = {
        "fragments": fragments_dict,
        "unlocated_fragments": unlocated_fragments_dict,
        "files": files_containing_fragments_set,
        "parameters": parameters_dict,
        "translation_units": translation_units_dict,
    }

    return result


def parse_M3_provides(m3):
    provides_data = m3["provides"]
    files_list = []
    for rel in provides_data:
        files_list.append(rel[0])
    files_list = list(dict.fromkeys(files_list))

    for file in files_list:
        files_list[files_list.index(file)] = re.sub("\\/.+\\/", "", file)
    return set(files_list)


def parse_M3_declaredType(m3):
    # methods, functions, variables
    methods_dict = {}
    functions_dict = {}
    variables_dict = {}

    declaredType_data = m3["declaredType"]
    for rel in declaredType_data:
        fragment = parse_M3_loc_statement(rel[0])

        match fragment["fragmentType"]:
            case constants.M3_CPP_METHOD_TYPE:
                fragment_info = rel[1]["returnType"]
                fragment["returnType"] = get_fragment_type(
                    fragment_info, get_fragment_type_key(fragment_info)
                )
                methods_dict[fragment["loc"]] = fragment
            case constants.M3_CPP_FUNCTION_TYPE:
                fragment_info = rel[1]["returnType"]
                fragment["returnType"] = get_fragment_type(
                    fragment_info, get_fragment_type_key(fragment_info)
                )
                functions_dict[fragment["loc"]] = fragment
            case constants.M3_CPP_VARIABLE_TYPE:
                fragment["type"] = get_fragment_type(
                    rel[1], get_fragment_type_key(rel[1])
                )
                variables_dict[fragment["simpleName"]] = fragment

    result = {
        "methods": methods_dict,
        "functions": functions_dict,
        "variables": variables_dict,
    }

    return result


def parse_M3_macro_expansions(m3):
    macro_expansions_data = m3["macroExpansions"]
    macros = {}

    def update_macro_fragment(macro_fragment, macro_location):
        number_of_expansions_in_file = macro_fragment["fileExpansions"].get(
            macro_location["file"], 0
        )
        macro_fragment["fileExpansions"][macro_location["file"]] = (
            number_of_expansions_in_file + 1
        )
        return macro_fragment

    for rel in macro_expansions_data:
        macro_location = get_fragment_declaration_location(rel[0])
        macro_fragment = parse_M3_loc_statement(rel[1])

        current_macro = macros.setdefault(
            macro_fragment["loc"],
            {
                "loc": macro_fragment["loc"],
                "fragmentType": macro_fragment["fragmentType"],
                "fileExpansions": {},
            },
        )

        current_macro = update_macro_fragment(current_macro, macro_location)

        macros[macro_fragment["loc"]] = current_macro

    return macros


def parse_M3_containment(m3):
    containment_data = m3["containment"]
    namespaces_dict = {}
    classes_dict = {}
    deferred_classes_dict = {}
    templates_dict = {}
    template_types_dict = {}
    specializations_dict = {}
    partial_specializations_dict = {}
    translation_unit_dict = {}
    functions_dict = {}
    contained_structures = {}

    containment_dicts = {
        constants.M3_CPP_NAMESPACE_TYPE: namespaces_dict,
        constants.M3_CPP_CLASS_TYPE: classes_dict,
        constants.M3_CPP_CLASS_TEMPLATE_TYPE: templates_dict,
        constants.M3_TEMPLATE_TYPE_PARAMETER_TYPE: template_types_dict,
        constants.M3_CPP_CLASS_SPECIALIZATION_TYPE: specializations_dict,
        constants.M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE: partial_specializations_dict,
        constants.M3_CPP_TRANSLATION_UNIT_TYPE: translation_unit_dict,
        constants.M3_CPP_FUNCTION_TYPE: functions_dict,
        constants.M3_CPP_DEFERRED_CLASS_TYPE: deferred_classes_dict
    }

    def update_namespace_fragment(namespace_fragment, contained_fragment):
        if (
            contained_fragment["fragmentType"]
            in constants.NAMESPACE_CHILD_FRAGMENT_TYPES
        ):
            namespace_fragment = update_fragment_contains(
                namespace_fragment, contained_fragment
            )
            update_or_add_fragment(contained_fragment)
        return namespace_fragment

    def update_translation_unit_fragment(translation_unit_fragment, contained_fragment):
        if contained_fragment["fragmentType"] in constants.LOGICAL_LOC_TYPES:
            translation_unit_fragment["definitions"].update(
                {contained_fragment["loc"]: contained_fragment}
            )
            update_or_add_fragment(contained_fragment)
        return translation_unit_fragment

    def update_or_add_fragment(fragment):
        fragment_type = fragment["fragmentType"]
        relevant_dict = containment_dicts[fragment_type]
        if fragment["loc"] not in relevant_dict:
            relevant_dict[fragment["loc"]] = fragment
    
    def update_fragment_contains(fragment, contained_fragment):

        contained_structures[child_fragment["fragmentType"] + ":" + child_fragment["loc"]] = child_fragment
        
        if fragment.get("contains") is not None:
            if contained_fragment["fragmentType"] + ":" + contained_fragment["loc"] not in [child["fragmentType"] + ":" + child["loc"] for child in fragment["contains"]]:
                fragment["contains"].append(contained_fragment)
        else:

            fragment["contains"] = [contained_fragment]

        return fragment

    for rel in containment_data:
        parent_fragment = parse_M3_loc_statement(rel[0])
        child_fragment = parse_M3_loc_statement(rel[1])

        match parent_fragment["fragmentType"]:
            case constants.M3_CPP_NAMESPACE_TYPE:
                namespace_fragment = containment_dicts[
                    constants.M3_CPP_NAMESPACE_TYPE
                ].get(parent_fragment["loc"], parent_fragment)
                namespace_fragment = update_namespace_fragment(
                    namespace_fragment, child_fragment
                )
                containment_dicts[constants.M3_CPP_NAMESPACE_TYPE][
                    parent_fragment["loc"]
                ] = namespace_fragment

            case constants.M3_CPP_TRANSLATION_UNIT_TYPE:
                translation_unit_fragment = containment_dicts[
                    constants.M3_CPP_TRANSLATION_UNIT_TYPE
                ].get(parent_fragment["loc"], parent_fragment)
                translation_unit_fragment.setdefault("definitions", {})
                translation_unit_fragment = update_translation_unit_fragment(
                    translation_unit_fragment, child_fragment
                )
                containment_dicts[constants.M3_CPP_TRANSLATION_UNIT_TYPE][
                    parent_fragment["loc"]
                ] = translation_unit_fragment

            case (
                constants.M3_CPP_CLASS_TYPE
                | constants.M3_CPP_CLASS_TEMPLATE_TYPE
                | constants.M3_TEMPLATE_TYPE_PARAMETER_TYPE
                | constants.M3_CPP_CLASS_SPECIALIZATION_TYPE
                | constants.M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE
                | constants.M3_CPP_DEFERRED_CLASS_TYPE
            ):
                relevant_dict = containment_dicts[parent_fragment["fragmentType"]]
                structure_fragment = relevant_dict.get(
                    parent_fragment["loc"], parent_fragment
                )

                if (
                    child_fragment["fragmentType"]
                    in constants.NESTED_STRUCTURES_FRAGMENT_TYPES
                ):
                    structure_fragment = update_fragment_contains(
                        structure_fragment, child_fragment
                    )

                relevant_dict[structure_fragment["fragmentType"] + ":" + structure_fragment["loc"]] = structure_fragment


    return containment_dicts, contained_structures


def parse_M3_callGraph(m3, operations):
    def matches_any_permitted_scheme(fragment_rel, allowed_schemes):
        return any(re.match(scheme, fragment_rel) for scheme in allowed_schemes)
    
    callGraph_data = m3["callGraph"]
    methodOverrides_data = m3["methodOverrides"]
    methodInvocation_data = m3['methodInvocations']
    overrides = {}
    invocations = {}
    unknown_operations = {}
    result = {}

    def process_invocation_relations(relations, edges, inverted_relation = False):
        for rel in relations:
            try:
                if (
                    r"message=Invalid%20type%20encountered%20in:" not in rel[1]
                    and r"message=Invalid%20type%20encountered%20in:" not in rel[0]
                ):
                    if (
                        matches_any_permitted_scheme(rel[0], constants.OPERATIONS_FRAGMENT_LOC_SCM)
                        and matches_any_permitted_scheme(rel[1], constants.OPERATIONS_FRAGMENT_LOC_SCM)
                    ):
                        source = parse_M3_loc_statement(rel[0]) if not inverted_relation else parse_M3_loc_statement(rel[1])

                        if source.get("loc") not in operations.keys():
                            unknown_operations[source.get("loc")] = source

                        target = parse_M3_loc_statement(rel[1]) if not inverted_relation else parse_M3_loc_statement(rel[0])

                        if target.get("loc") not in operations.keys():
                            unknown_operations[target.get("loc")] = target

                        invocation_id = source.get("loc") + "--" + target.get("loc")

                        existing_invocation = edges.get(invocation_id)
                        if existing_invocation is None:
                            invocation = {}
                            invocation["id"] = invocation_id
                            invocation["source"] = source
                            invocation["target"] = target
                            invocation["weight"] = 1

                            invocations[invocation_id] = invocation
                        else:
                            logging.debug("updating weight of existing invocation")
                            existing_invocation["weight"] += 1
                            edges[invocation_id] = existing_invocation

            except Exception as e:
                logging.error("exception: %s", e)
            
        return edges

    invocations = process_invocation_relations(callGraph_data, invocations)
    print(f"length of invocation list after callGraph:{len(invocations)}")
    invocations = process_invocation_relations(methodInvocation_data, invocations)
    print(f"length of invocation list after methodInvocations:{len(invocations)}")
    overrides = process_invocation_relations(methodOverrides_data, overrides, inverted_relation=True)
    print(f"length of overrides list:{len(overrides)}")

    if len(unknown_operations) > 0:
        logging.debug(
            "[VERBOSE] Found %s unknown operations when parsing callGraph",
            len(unknown_operations),
        )

    result = {
        "invocations": invocations,
        "overrides": overrides,
        "unknown_operations": unknown_operations,
    }

    return result


def parse_M3_extends(m3, fragments, fragments_type):
    extension_counter = 0

    logging.debug("Adding extensions for structure type: %s", fragments_type)

    extends_data = m3["extends"]

    # Create a copy of the dictionary items to iterate over
    fragments_copy = list(fragments.items())

    for fragment in fragments_copy:  # Iterate over the copied list of items
        for rel in extends_data:
            extending_fragment = parse_M3_loc_statement(rel[0])
            if fragment[1].get("loc") == extending_fragment.get("loc"):
                base_fragment = parse_M3_loc_statement(rel[1])

                if base_fragment.get("fragmentType") != "unsupported":
                    if fragment[1].get("extends") is None:
                        fragment[1]["extends"] = [base_fragment]
                    else:
                        fragment[1]["extends"].append(base_fragment)
                
                # Modify the original dictionary outside of the loop
                fragments[fragment[1]["loc"]] = fragment[1]
                extension_counter += 1


    logging.debug("Added %s extensions", extension_counter)

    return fragments


def parse_M3_loc_statement(loc_statement: str) -> Dict[str, Any]:
    fragment = {}

    fragment_loc_schema = re.match(constants.M3_SCHEMA_REGEX, loc_statement)
    if not fragment_loc_schema:
        return {"fragmentType": constants.UNSUPPORTED_TYPE}

    fragment_type = fragment_loc_schema[0].split(":///")[0]

    def parse_and_set_fragment(fragment_type, schema):
        loc_path, fragment_parent, simple_name = parse_rascal_loc(loc_statement, schema)
        fragment["loc"] = loc_path
        fragment["fragmentType"] = fragment_type
        fragment["simpleName"] = simple_name

        if fragment_type in {
            constants.M3_CPP_FUNCTION_TYPE,
            constants.M3_CPP_METHOD_TYPE,
            constants.M3_CPP_FUNCTION_TEMPLATE_TYPE,
            constants.M3_DEFERRED_FUNCTION_TYPE
        }:
            fragment["parent"] = fragment_parent

        elif fragment_type == constants.M3_CPP_NAMESPACE_TYPE:
            fragment["loc"] = loc_path or "UnnamedNamespace"
            fragment["simpleName"] = simple_name or "UnnamedNamespace"

    # Handle known fragment types
    if fragment_type in constants.FRAGMENT_PARSERS:
        parse_and_set_fragment(fragment_type, constants.FRAGMENT_PARSERS[fragment_type])
    else:
        # Unsupported fragment type
        fragment["fragmentType"] = constants.UNSUPPORTED_TYPE

    return fragment


def parse_rascal_loc(loc, schema=None):
    loc_fragment_parent = ""

    if schema is not None:
        loc_path = re.sub(schema, "", loc)
    else:
        loc_path = loc

    parsed_loc = re.split("/", loc_path)
    loc_fragment = parsed_loc[-1]

    if len(parsed_loc) > 1:
        loc_fragment_parent = "/".join(parsed_loc[:-1])

        if loc_fragment == "":
            loc_fragment_parent = "/".join(parsed_loc[:-2])
            loc_fragment = parsed_loc[-2]

    if re.search(r"\(|\)", loc_fragment):
        loc_fragment = re.split("\\(", loc_fragment)[0]

    return loc_path, loc_fragment_parent, loc_fragment


def parse_rascal_problem_loc(problem_loc):
    try:
        loc_path = re.sub(constants.M3_PROBLEM_LOC_SCM, "", problem_loc)
        id_and_message = loc_path.split("?message=")

        if len(id_and_message) == 2:
            # Extract the ID and message
            location_id, error_message = id_and_message

            error_message = error_message.replace("%20", " ")
            error_message_list = error_message.split(":")
            if len(error_message_list) == 2:
                error_object = error_message_list[1].replace(" ", "")
            else:
                error_object = ""

            return {
                "loc_path": loc_path,
                "id": location_id,
                "message": error_message,
                "object": error_object,
            }
        else:
            return None  # Invalid format
    except Exception as e:

        return None


def get_fragment_declaration_location(declaration_loc):
    location = {}

    location["file"], location["position"] = re.split("\\(", declaration_loc)
    location["file"] = re.sub(constants.M3_FILE_LOC_SCM, "", location.get("file"))[:-1]
    location["position"] = "(" + location["position"]

    return location


def get_fragment_type_key(fragment_field):
    try:
        if "baseType" in fragment_field.keys():
            return "baseType"
        if "decl" in fragment_field.keys():
            return "decl"
        if "type" in fragment_field.keys():
            return "type"
        if "msg" in fragment_field.keys():
            return "msg"
        if "templateArguments" in fragment_field.keys():
            return None
    except:
        return None


def get_fragment_type(element, field):
    if get_fragment_type_key(element.get(field)) is not None:
        return get_fragment_type(element[field], get_fragment_type_key(element[field]))
    else:
        if field == "baseType":
            return element[field]
        if field == "decl":
            if re.match(constants.M3_CPP_CLASS_TEMPLATE_TYPE, element[field]):
                return "string"
            else:
                elementParts = re.split(
                    "\\/", re.sub(constants.M3_CLASS_LOC_SCM, "", element[field])
                )
                return elementParts[len(elementParts) - 1]
        if field == "msg":
            return None


def get_parameter_type(element, field):
    if field == "decl":
        return re.sub("cpp\\+class:\\/+", "", element[field])
    if field == "type":
        if "decl" in element[field].keys():
            if (
                element[field]["decl"]
                == "cpp+classTemplate:///std/__cxx11/basic_string"
            ):
                return "string"
            else:
                return re.sub("cpp\\+class:\\/+", "", element[field]["decl"])
        if "baseType" in element[field].keys():
            return element[field]["baseType"]
        if "modifiers" in element[field].keys():
            pass
    if field == "baseType":
        return element[field]


def update_parameter_info(parameter, rel):
    parameter["function"] = re.split("\\(", re.split("/", rel[0])[-2])[0]
    loc_path = re.sub(constants.M3_PARAMETER_LOC_SCM, "", rel[0])
    loc_path_list = loc_path.split("/")
    parameter["simpleName"] = loc_path_list[-1]

    if parameter["simpleName"] == "":
        return None
    else:
        parameter["location"] = int(
            re.split(",", re.sub("\\|file:\\/+.+\\|\\(", "", rel[1]))[0]
        )
        function_path = "/".join(loc_path_list[1:-1])

        function_path = loc_path_list[0] + function_path
        parameter["functionLoc"] = function_path

        return parameter


def is_fragment_parsed(fragment, fragments):
    return bool(fragments.get(fragment["simpleName"]) is not None)
