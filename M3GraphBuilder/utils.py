import os
import logging
import configparser


def get_and_validate_output_folder(config ,output_folder_arg, graph_folder_name):
    """Validate the output folder taken from the provided arguments, or the configuration."""
    output_folder = (
        output_folder_arg
        if output_folder_arg
        else config["output"]["path"] + "/" + graph_folder_name + "/"
    )
    validate_dir(output_folder)
    return output_folder


def setup_logging(config, log_name):
    """Set up logging to write logs to a specific file path."""

    log_file_path = config.get("logging").get("path")
    if not log_file_path:
        log_file_path = os.path.dirname(os.path.dirname(os.curdir)).join("\\logs")

    validate_dir(log_file_path)

    logging.basicConfig(
        level=logging.INFO,  # Set the minimum log level
        format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
        handlers=[
            logging.FileHandler(
                f"{log_file_path}\\{log_name}", mode="a"
            ),  # Append logs to the file
            logging.StreamHandler(),  # Also output logs to the console
        ],
    )


def validate_dir(path):
    """If directory does not exist create it."""
    if not os.path.exists(path):
        os.makedirs(path)


def load_config_from_ini_file():
    """Load configuration from an INI file located in the same directory as the script."""
    app_root = os.path.dirname(os.path.abspath(__file__))
    app_root_parent = os.path.join(app_root, os.pardir)
    config_path = os.path.join(app_root, "config.ini")
    config_dict = {}

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)

    # Resolve paths from the config file
    input_path = os.path.join(app_root_parent, config.get("input", "path"))
    output_path = os.path.join(app_root_parent, config.get("output", "path"))
    log_path = os.path.join(app_root_parent, config.get("logging", "path"))

    config_dict["project"] = {
        "name": config.get("project", "name"),
        "desc": config.get("project", "desc")
    }
    config_dict["output"] ={ "path": output_path } 
    config_dict["logging"] = { 
        "path": log_path, 
        "verbose": config.get("logging", "verbose") }


    return config_dict


def get_model_file_name(file_path):
    """Extract the base name of a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError("Invalid file path. File does not exist.")
    if not file_path.endswith(".json"):
        raise ValueError("--model_path must lead to a file with a JSON extension.")
    return os.path.splitext(os.path.basename(file_path))[0]
