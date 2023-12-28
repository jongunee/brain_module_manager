import yaml


def load_config():
    config_file = "config.yaml"
    if config_file:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    base_files_dir = config["paths"]["base_files_dir"]
    base_models_dir = config["paths"]["base_models_dir"]
    server_info = {}

    return base_files_dir, base_models_dir, server_info


def load_db_info():
    config_file = "config.yaml"
    if config_file:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    db_uri = config["database"]["uri"]
    db_name = config["database"]["name"]
    db_collection_metadata = config["database"]["collection_metadata"]
    db_collection_modeldata = config["database"]["collection_modeldata"]

    return db_uri, db_name, db_collection_metadata, db_collection_modeldata
