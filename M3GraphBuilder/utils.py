import os
import logging
import configparser


def setup_logging(config, log_name):
    """Set up logging to write logs to a specific file path."""

    log_file_path = config.get("logging").get("path")
    if not log_file_path:
        log_file_path = os.path.dirname(os.path.dirname(os.curdir)).join("\\logs")

    validate_dir(log_file_path)

    # Set up the logging configuration
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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.ini")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)
    return {section: dict(config.items(section)) for section in config.sections()}


def get_model_file_name(file_path):
    """Extract the base name of a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError("Invalid file path. File does not exist.")
    if not file_path.endswith(".json"):
        raise ValueError("--model_path must lead to a file with a JSON extension.")
    return os.path.splitext(os.path.basename(file_path))[0]
