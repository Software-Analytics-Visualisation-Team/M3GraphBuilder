import re
import M3GraphBuilder.converters.constants as constants


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


def parse_M3_declarations(m3, fragments_dict=None):
    declarations_data = m3["declarations"]
    unlocated_fragments_dict = {}
    parameters_dict = {}
    files_containing_fragments_set = set()

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
                    # else:
                    #     print("[DEBUG] empty parameter processed:")
                    #     print(rel[0])

        else:
            for key in fragments_dict.keys():
                if fragments_dict[key].get("simpleName") == declarations_fragment.get(
                    "simpleName"
                ):
                    fragments_dict[key]["location"] = get_fragment_declaration_location(
                        rel[1]
                    )

            for fragment in fragments_dict.items():
                location = fragment[1].get("location")
                if location is None:
                    unlocated_fragments_dict[fragment[1].get("simpleName")] = fragment[
                        1
                    ]
                else:
                    files_containing_fragments_set.add(location["file"])

    result = {
        "fragments": fragments_dict,
        "unlocated_fragments": unlocated_fragments_dict,
        "files": files_containing_fragments_set,
        "parameters": parameters_dict,
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
                methods_dict[fragment["simpleName"]] = fragment
            case constants.M3_CPP_FUNCTION_TYPE:
                fragment_info = rel[1]["returnType"]
                fragment["returnType"] = get_fragment_type(
                    fragment_info, get_fragment_type_key(fragment_info)
                )
                functions_dict[fragment["simpleName"]] = fragment
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


def parse_M3_containment(m3):
    containment_data = m3["containment"]
    namespaces_dict = {}
    classes_dict = {}
    templates_dict = {}
    template_types_dict = {}
    specializations_dict = {}
    partial_specializations_dict = {}
    translation_unit_dict = {}

    for rel in containment_data:
        fragment = parse_M3_loc_statement(rel[0])

        match fragment["fragmentType"]:
            case constants.M3_CPP_CLASS_TYPE | constants.M3_CPP_DEFERRED_CLASS_TYPE:
                classes_dict[fragment["simpleName"]] = fragment
            case constants.M3_CPP_NAMESPACE_TYPE:
                namespaces_dict[fragment["simpleName"]] = fragment
                contained_fragment = parse_M3_loc_statement(rel[1])
                if (
                    contained_fragment.get("fragmentType")
                    in constants.NAMESPACE_CHILD_FRAGMENT_TYPES
                ):
                    namespaces_dict[fragment["simpleName"]] = (
                        get_fragment_with_contains(
                            namespaces_dict[fragment["simpleName"]],
                            contained_fragment["simpleName"],
                        )
                    )
            case constants.M3_CPP_CLASS_TEMPLATE_TYPE:
                templates_dict[fragment["simpleName"]] = fragment
            case constants.M3_TEMPLATE_TYPE_PARAMETER_TYPE:
                template_types_dict[fragment["simpleName"]] = fragment
            case constants.M3_CPP_CLASS_SPECIALIZATION_TYPE:
                specializations_dict[fragment["simpleName"]] = fragment
            case constants.M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE:
                partial_specializations_dict[fragment["simpleName"]] = fragment
            case constants.M3_CPP_TRANSLATION_UNIT_TYPE:
                translation_unit_dict[fragment["simpleName"]] = fragment
                contained_fragment = parse_M3_loc_statement(rel[1])
                if (
                    contained_fragment.get("fragmentType")
                    in constants.NAMESPACE_CHILD_FRAGMENT_TYPES
                ):
                    translation_unit_dict[fragment["simpleName"]] = (
                        get_fragment_with_contains(
                            translation_unit_dict[fragment["simpleName"]],
                            contained_fragment["simpleName"],
                        )
                    )

    result_dict = {
        "namespaces": namespaces_dict,
        "classes": classes_dict,
        "templates": templates_dict,
        "template_types": template_types_dict,
        "specializations": specializations_dict,
        "partial_specializations": partial_specializations_dict,
        "translation_units": translation_unit_dict,
    }

    return result_dict


def parse_M3_callGraph(m3, operations):
    callGraph_data = m3["callGraph"]
    invokes = []

    for operation in operations.items():
        for rel in callGraph_data:
            # if re.match(".+\\.", operation[0]):
            #     source = operation[0].replace(".", "/")
            # else:
            source = operation[0]

            if source in rel[0]:
                invoke = {}
                invoke["source"] = source
                try:
                    if re.match(constants.M3_FUNCTION_LOC_SCM, rel[1]) or re.match(
                        constants.M3_METHOD_LOC_SCM, rel[1]
                    ):
                        # target = re.sub("cpp\\+function:\\/+.+\\/", "", rel[1])
                        fragment = parse_M3_loc_statement(rel[1])
                        target = fragment.get("simpleName")

                    # elif re.match(constants.M3_METHOD_LOC_SCM, target):
                    #     target = re.sub("cpp\\+method:\\/+", "", rel[1])
                    #     target = target.replace("/", ".")
                    # target = re.split("\\(", target)[0]

                    if target in operations.keys():
                        invoke["target"] = target
                        invokes.append(invoke)
                except:
                    pass
            else:
                pass

    return invokes


def parse_M3_extends(m3, fragments):
    extends_data = m3["extends"]
    for fragment in fragments:
        for rel in extends_data:
            extending_fragment = parse_M3_loc_statement(rel[0])
            if fragment == extending_fragment:
                base_fragment = parse_M3_loc_statement(rel[1])
                fragment["extends"] = base_fragment["simpleName"]
                fragments[fragment["simpleName"]] = fragment

    return fragments


def parse_M3_loc_statement(loc_statement):
    fragment = {}

    fragment_loc_schema = re.match(constants.M3_SCHEMA_REGEX, loc_statement)
    fragment_type = fragment_loc_schema[0].split(":///")[0]

    match fragment_type:
        case constants.M3_CPP_CLASS_TYPE:  # parse class loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_CLASS_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_CLASS_TYPE
            fragment["loc"] = loc_path
        case constants.M3_CPP_CONSTRUCTOR_TYPE:  # parse constructor loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_CONSTRUCTOR_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_CONSTRUCTOR_TYPE
            fragment["loc"] = loc_path
        case constants.M3_CPP_FUNCTION_TYPE:  # parse function loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_FUNCTION_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_FUNCTION_TYPE
            fragment["loc"] = loc_path
        case constants.M3_CPP_FUNCTION_TEMPLATE_TYPE:  # parse functionTemplate loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_FUNCTION_TEMPLATE_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_FUNCTION_TEMPLATE_TYPE
            fragment["loc"] = loc_path
        case constants.M3_CPP_METHOD_TYPE:  # parse method loc
            loc_path, fragment_class, fragment_name = parse_rascal_method_loc(
                loc_statement
            )
            fragment["simpleName"] = fragment_name
            fragment["fragmentType"] = constants.M3_CPP_METHOD_TYPE
            fragment["loc"] = loc_path

            fragment["class"] = fragment_class
        case constants.M3_CPP_NAMESPACE_TYPE:  # parse namespace loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_NAMESPACE_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_NAMESPACE_TYPE
            fragment["loc"] = loc_path
        case constants.M3_CPP_DEFERRED_CLASS_TYPE:  # parse deferredClassInstance loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_DEFFERED_CLASS_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_DEFERRED_CLASS_TYPE
            fragment["loc"] = loc_path
        case constants.M3_CPP_CLASS_TEMPLATE_TYPE:  # parse classTemplate loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_CLASS_TEMPLATE_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_CLASS_TEMPLATE_TYPE
            fragment["loc"] = loc_path
        case (
            constants.M3_TEMPLATE_TYPE_PARAMETER_TYPE
        ):  # parse templateTypeParameter loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_TEMPLATE_TYPE_PARAM_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_TEMPLATE_TYPE_PARAMETER_TYPE
            fragment["loc"] = loc_path
        case (
            constants.M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE
        ):  # parse classTemplatePartialSpec loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_CLASS_TEMPLATE_PARTIAL_SPEC_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE
            fragment["loc"] = loc_path
        case (
            constants.M3_CPP_CLASS_SPECIALIZATION_TYPE
        ):  # parse classSpecialization loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_CLASS_SPECIALIZATION_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_CLASS_SPECIALIZATION_TYPE
            fragment["loc"] = loc_path
        case constants.M3_CPP_TRANSLATION_UNIT_TYPE:  # parse translationUnit loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_TRANSLATION_UNIT_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_TRANSLATION_UNIT_TYPE
            fragment["loc"] = loc_path
        case constants.M3_PROBLEM_TYPE:  # parse problem loc
            parsed_problem_loc = parse_rascal_problem_loc(loc_statement)
            if parsed_problem_loc.get("object") is not None:
                fragment["simpleName"] = parsed_problem_loc.get("object")
            else:
                fragment["simpleName"] = parsed_problem_loc.get("id")
            fragment["fragmentType"] = constants.M3_PROBLEM_TYPE
            fragment["loc"] = parsed_problem_loc.get("loc_path")
        case constants.M3_CPP_VARIABLE_TYPE:  # parse variable loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_VARIABLE_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_VARIABLE_TYPE
            fragment["loc"] = loc_path
        case constants.M3_CPP_PARAMETER_TYPE:  # parse parameter loc
            loc_path, simple_name = parse_rascal_loc(
                constants.M3_PARAMETER_LOC_SCM, loc_statement
            )
            fragment["simpleName"] = simple_name
            fragment["fragmentType"] = constants.M3_CPP_PARAMETER_TYPE
            fragment["loc"] = loc_path
        case _:
            fragment["fragmentType"] = constants.UNSUPPORTED_TYPE

    return fragment


def parse_rascal_loc(schema, loc):

    loc_path = re.sub(schema, "", loc)
    parsed_loc = re.split("/", loc_path)
    loc_fragment = parsed_loc[-1]

    if loc_fragment == "":
        loc_fragment = parsed_loc[-2]

    if re.search(r"\(|\)", loc_fragment):
        loc_fragment = re.split("\\(", loc_fragment)[0]

    return loc_path, loc_fragment


def parse_rascal_method_loc(method_loc):

    loc_path = re.sub(constants.M3_METHOD_LOC_SCM, "", method_loc)
    parsed_loc = re.split("/", loc_path)
    method_loc_class = parsed_loc[-2]
    method_loc_fragment = parsed_loc[-1]

    if method_loc_fragment == "":
        method_loc_class = parsed_loc[-3]
        method_loc_fragment = parsed_loc[-2]

    if re.search(r"\(|\)", method_loc_fragment):
        method_loc_fragment = re.split("\\(", method_loc_fragment)[0]

    return loc_path, method_loc_class, method_loc_fragment


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
    location["file"] = re.sub("\\|file:.+/", "", location.get("file"))[:-1]
    location["position"] = "(" + location["position"]

    return location


def get_fragment_with_contains(fragment, contained_fragment_name):

    if fragment.get("contains") is not None:

        fragment["contains"].append(contained_fragment_name)
    else:

        fragment["contains"] = [contained_fragment_name]

    return fragment


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
