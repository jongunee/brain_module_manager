import yaml


def load_config():
    config_file = "config.yaml"
    if config_file:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    base_files_dir = config["base_files_dir"]
    base_models_dir = config["base_models_dir"]
    server_info = {}

    return base_files_dir, base_models_dir, server_info


def load_meta_data():
    config_file = "config.yaml"
    if config_file:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    metadata_file = config["metadata_file"]

    return metadata_file
