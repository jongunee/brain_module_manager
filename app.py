from flask import Flask, render_template, request, jsonify
import socket
import subprocess
import os
import json
import tempfile
import random
import bentoml
import torch
import keras
import joblib
import tensorflow as tf
import zipfile
import yaml
from werkzeug.utils import secure_filename
from datetime import datetime


app = Flask(__name__)

base_files_dir = "models"
metadata_file = "metadata.json"
config_file = "config.yaml"


if config_file:
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

# config 설정 로드
base_models_dir = config["base_models_dir"]

# 현재 사용가능한 포트를 찾아 사용가능한 랜덤 포트 찾기
server_info = {}


def find_available_port(start_port, end_port):
    while True:
        trial_port = random.randint(start_port, end_port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            port_is_used = sock.connect_ex(("localhost", trial_port)) == 0
            if not port_is_used:
                return trial_port


def update_metadata(filename, framework, extension, input_type, output_type):
    if not os.path.exists(metadata_file):
        data = {}
    else:
        with open(metadata_file, "r") as f:
            data = json.load(f)

    model_name = filename.rsplit(".", 1)[0]  # 파일 확장자를 제거하여 모델명을 얻음
    current_date = datetime.now().strftime("%Y-%m-%d")
    data[model_name] = {
        "framework": framework,
        "extension": extension,
        "input_type": input_type,
        "output_type": output_type,
        "uploaded_date": current_date,
    }

    with open(metadata_file, "w") as f:
        json.dump(data, f, indent=2)


def read_metadata():
    if not os.path.exists(metadata_file):
        return []

    with open(metadata_file, "r") as f:
        data = json.load(f)

    file_list = []
    for model_name, metadata in data.items():
        file_info = {
            "model_name": model_name,
            "framework": metadata["framework"],
            "extension": metadata["extension"],
            "input_type": metadata["input_type"],
            "output_type": metadata["output_type"],
            "uploaded_date": metadata["uploaded_date"],
        }
        file_list.append(file_info)

    return file_list


# 저장된 학습 모델 리스트 찾기


def get_saved_models(base_models_dir):
    all_model_info = []
    for model_name in os.listdir(base_models_dir):
        model_base_dir = os.path.join(base_models_dir, model_name)
        if os.path.isdir(model_base_dir):
            for tag_name in os.listdir(model_base_dir):
                sub_model_dir = os.path.join(model_base_dir, tag_name)
                if os.path.isdir(sub_model_dir):
                    all_model_info.append((model_name, tag_name, "", "", ""))
    return all_model_info


def save_with_bento(framework, file_path, bento_model_name):
    root, extension = os.path.splitext(file_path)
    print(extension)
    if framework == "sklearn":
        model = joblib.load(file_path)
        return bentoml.sklearn.save_model(bento_model_name, model)
    elif framework == "keras":
        model = keras.models.load_model(file_path)
        return bentoml.keras.save_model(bento_model_name, model)
    elif framework == "tensorflow":
        if extension == ".h5":
            model = keras.models.load_model(file_path)
            return bentoml.keras.save_model(bento_model_name, model)
        else:
            model = tf.saved_model.load(file_path)
            return bentoml.tensorflow.save_model(bento_model_name, model)
    elif framework == "pytorch":
        model = torch.load(file_path)
        return bentoml.pytorch.save_model(bento_model_name, model)
    else:
        return "Unsupported framework: {}".format(framework)


@app.route("/create", methods=["POST"])
def create_model():
    data = request.get_json()
    model_name = data.get("model_name")
    framework = data.get("framework")
    extension = data.get("extension")

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
    bento_model_name = "bento_" + model_name
    save_with_bento(framework, file_path, bento_model_name)

    return jsonify(model_name=bento_model_name)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/files")
def files():
    saved_files = read_metadata()
    return render_template("file_list.html", saved_files=saved_files)


@app.route("/models")
def models():
    # base_models_dir = r"C:\Users\whsrj\bentoml\models"
    saved_models = get_saved_models(base_models_dir)
    return render_template("model_list.html", saved_models=saved_models)


@app.route("/servers")
def servers():
    return render_template("server_list.html", server_info=server_info)


@app.route("/upload", methods=["POST"])
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

    filename = secure_filename(file.filename)
    file_path = os.path.join(base_files_dir, filename)
    file.save(file_path)
    update_metadata(filename, framework, extension, input_type, output_type)

    return f"Model file uploaded successfully with framework {framework}"


@app.route("/service", methods=["POST"])
def service():
    serve_file = "service"
    port = find_available_port(2000, 3000)
    ip = "127.0.0.1"

    # body에 포함된 데이터를 'config_data'로 받기
    config_data = request.json
    # print("Received config_data:", config_data)

    # 임시 파일 생성
    config_file = tempfile.NamedTemporaryFile(delete=False)
    config_file.write(json.dumps(config_data).encode("utf-8"))
    config_file.close()

    cmd = f"bentoml serve {serve_file}:svc --host {ip} --port {port} --reload"

    # 서브 프로세스를 실행해서 환경변수로 전달
    with tempfile.NamedTemporaryFile(delete=False) as config_file:
        config_filepath = config_file.name
        with open(config_filepath, "w") as f:
            json.dump(config_data, f)
        env_vars = os.environ.copy()
        env_vars["CONFIG_PATH"] = config_filepath
        subprocess.Popen(cmd.split(), env=env_vars)

    model_name = config_data["model_name"]

    if model_name not in server_info:
        server_info[model_name] = []

    server_info[model_name].append({"config_data": config_data, "ip": ip, "port": port})
    print(server_info)

    return f"Started service: {serve_file} on port {port}"


@app.route("/info", methods=["GET"])
def info():
    return server_info


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
