from flask import Blueprint, request, jsonify, render_template, current_app
from werkzeug.utils import secure_filename
from config import load_config
from .bentoize import save_with_bento
from . import utils
from bson.json_util import dumps
import os
import tempfile
import zipfile
import subprocess
import json
import bentoml
import yaml
import docker

bp = Blueprint("main", __name__)

base_files_dir, base_models_dir, server_info = load_config()


@bp.route("/create", methods=["POST"])
def create_model():
    data = request.get_json()
    model_name = data.get("model_name")
    framework = data.get("framework")
    extension = data.get("extension")
    input_type = data.get("input_type")
    output_type = data.get("output_type")
    api_data = data.get("api_data")

    if not model_name or not extension:
        return "Model name and extension are required", 400

    if extension == "saved_model":
        file_path = os.path.join(base_files_dir, model_name)
        if not os.path.isdir(file_path):
            zip_file = zipfile.ZipFile(file_path + ".zip")
            zip_file.extractall(file_path)
            zip_file.close()
    else:
        file_path = os.path.join(base_files_dir, model_name + extension)

    if not os.path.exists(file_path):
        return "File not found", 404

    # 모델을 로드하고 BentoML로 저장
    # bento_model_name = "bento_" + model_name
    result = save_with_bento(
        file_path, framework, model_name, input_type, output_type, api_data
    )
    print("result: ", result)
    return jsonify(model_name=model_name)


@bp.route("/")
def home():
    return render_template("index.html")


@bp.route("/files")
def files():
    metadata = utils.read_metadata_db()
    return render_template("file_list.html", metadata=metadata)


@bp.route("/models")
def models():
    # base_models_dir = r"C:\Users\whsrj\bentoml\models"
    # saved_models = utils.get_saved_models(base_models_dir)
    saved_models = utils.read_modeldata_db()
    return render_template("model_list.html", saved_models=saved_models)


@bp.route("/servers")
def servers():
    return render_template("server_list.html", server_info=server_info)


@bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    framework = request.form.get("framework")
    if not framework:
        return "Framework not selected", 400

    extension = request.form.get("extension")
    if not extension:
        return "Extension not selected", 400

    input_type = request.form.get("input_type")
    if not input_type:
        return "Input type not selected", 400

    output_type = request.form.get("output_type")
    if not output_type:
        return "Output type not selected", 400

    api_data = request.form.get("api_data")
    if not api_data:
        return "api data not entered", 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(base_files_dir, filename)
    file.save(file_path)
    print("file name:", filename)
    utils.update_metadata_db(
        filename, framework, extension, input_type, output_type, api_data
    )

    return f"Model file uploaded successfully with framework {framework}"


@bp.route("/service", methods=["POST"])
def service():
    serve_file = "service"
    port = utils.find_available_port(2000, 3000)
    ip = "127.0.0.1"

    # body에 포함된 데이터를 'config_data'로 받기
    config_data = request.json
    # print("Received config_data:", config_data)

    # 임시 파일 생성
    config_file = tempfile.NamedTemporaryFile(delete=False)
    config_file.write(json.dumps(config_data).encode("utf-8"))
    config_file.close()

    service_directory = "./app/"
    cmd = f"bentoml serve {serve_file}:svc --host {ip} --port {port} --reload"

    # 서브 프로세스를 실행해서 환경변수로 전달
    with tempfile.NamedTemporaryFile(delete=False) as config_file:
        config_filepath = config_file.name
        with open(config_filepath, "w") as f:
            json.dump(config_data, f)
        env_vars = os.environ.copy()
        env_vars["CONFIG_PATH"] = config_filepath
        subprocess.Popen(cmd.split(), env=env_vars, cwd=service_directory)

    model_name = config_data["model_name"]

    if model_name not in server_info:
        server_info[model_name] = []

    server_info[model_name].append({"config_data": config_data, "ip": ip, "port": port})
    # print(server_info)

    return f"Started service: {serve_file} on port {port}"


@bp.route("/images", methods=["GET", "POST"])
def images():
    if request.method == "GET":
        client = docker.from_env()
        saved_images = []
        for image in client.images.list():
            saved_images.append(image.tags[0])
        return render_template("image_list.html", saved_images=saved_images)

    elif request.method == "POST":
        config_data = request.json
        if config_data["framework"] == "sklearn":
            model_package = "scikit-learn"
        elif config_data["framework"] == "keras":
            model_package = "keras"
        elif config_data["framework"] == "pytorch":
            model_package = "torch"
        elif config_data["framework"] == "tensorflow":
            model_package = "tensorflow"
        service_name = config_data["model_name"].split(":")[0]

        print("****config_data: ", config_data)
        # config_data["api_data"] = json.dumps(config_data["api_data"])
        # print("****config_data: ", config_data)

        with open("model_config.yaml", "w") as f:
            yaml.dump(config_data, f)
        bentoml.bentos.build(
            service="service_for_docker.py:svc",
            # version="0.6",  # override default version generator
            # description=open("README.md").read(),
            include=["service_for_docker.py", "model_config.yaml"],
            exclude=[],  # files to exclude can also be specified with a .bentoignore file
            python=dict(
                packages=["pandas", "numpy", "pydantic", model_package],
            ),
            docker=dict(
                distro="debian",
                python_version="3.10",
            ),
        )
        bento_name = service_name + ":latest"
        print("bento_name: ", bento_name)

        bentoml.container.build(bento_name)
        return f"image created"


# 프론트엔드 API
@bp.route("/api/files")
def apiFiles():
    metadata = utils.read_metadata_db()
    metadata_list = list(metadata)
    return jsonify(dumps(metadata_list))


@bp.route("/api/models")
def apiModels():
    modeldata = utils.read_modeldata_db()
    modeldata_list = list(modeldata)
    return jsonify(dumps(modeldata_list))


@bp.route("/api/images")
def apiImages():
    client = docker.from_env()
    image_list = []
    for image in client.images.list():
        image_list.append(image.tags[0])
    return jsonify(image_list)
