M3_PROBLEM_TYPE = r"problem"
M3_CPP_NAMESPACE_TYPE = r"cpp+namespace"
M3_CPP_CLASS_TYPE = r"cpp+class"
M3_CPP_DEFERRED_CLASS_TYPE = r"cpp+deferredClassInstance"
M3_CPP_CLASS_TEMPLATE_TYPE = r"cpp+classTemplate"
M3_TEMPLATE_TYPE_PARAMETER_TYPE = r"cpp+templateTypeParameter"
M3_CPP_CLASS_SPECIALIZATION_TYPE = r"cpp+classSpecialization"
M3_CPP_CLASS_TEMPLATE_PARTIAL_SPEC_TYPE = r"cpp+classTemplatePartialSpec"
M3_CPP_FUNCTION_TYPE = r"cpp+function"
M3_CPP_FUNCTION_TEMPLATE_TYPE = r"cpp+functionTemplate"
M3_CPP_METHOD_TYPE = r"cpp+method"
M3_CPP_CONSTRUCTOR_TYPE = r"cpp+constructor"
M3_CPP_VARIABLE_TYPE = r"cpp+variable"
M3_CPP_TRANSLATION_UNIT_TYPE = r"cpp+translationUnit"
UNSUPPORTED_TYPE = r"unsupported"

# Regex expression constants
M3_CLASS_LOC_SCM = r"cpp+class:///"
M3_DEFFERED_CLASS_LOC_SCM = r"cpp+deferredClassInstance:///"
M3_CONSTRUCTOR_LOC_SCM = r"cpp+constructor:///"
M3_DESTRUCTOR_LOC_SCM = r"cpp+destructor:///"
M3_PROBLEM_LOC_SCM = r"problem:///"
M3_CLASS_TEMPLATE_LOC_SCM = r"cpp+classTemplate:///"
M3_CLASS_SPECIALIZATION_LOC_SCM = r"cpp+classSpecialization:///"
M3_TEMPLATE_TYPE_PARAM_LOC_SCM = r"cpp+templateTypeParameter:///"
M3_CLASS_TEMPLATE_PARTIAL_SPEC_LOC_SCM = r"cpp+classTemplatePartialSpec:///"
M3_PARAMETER_LOC_SCM = r"cpp+parameter:/"
M3_FILE_LOC_SCM = r"|file:///"
M3_FUNCTION_LOC_SCM = r"cpp+function:///"
M3_FUNCTION_TEMPLATE_LOC_SCM = r"cpp+functionTemplate:///"
M3_VARIABLE_LOC_SCM = r"cpp+variable:///"
M3_FUNCTION_LOC_SCM = r"cpp+field:///"
M3_METHOD_LOC_SCM = r"cpp+method:///"
M3_NAMESPACE_LOC_SCM = r"cpp+namespace:///"
M3_TRANSLATION_UNIT_LOC_SCM = r"cpp+translationUnit:///"


FULL_FILE_PATH_REGEX = f"{M3_FILE_LOC_SCM}.+/"
FULL_PATH_REGEX = "+.+/"
M3_SCHEMA_REGEX = ".+:///"

# Allowed rel
NAMESPACE_CHILD_FRAGMENT_TYPES = [M3_CPP_NAMESPACE_TYPE]
# NAMESPACE_CHILD_FRAGMENT_TYPES = [M3_CPP_NAMESPACE_TYPE, M3_CPP_CLASS_TYPE, M3_CPP_CLASS_TEMPLATE_TYPE, M3_CPP_FUNCTION_TYPE, M3_CPP_FUNCTION_TEMPLATE_TYPE] #TODO:Extend when ClassViz can handle this situation.
