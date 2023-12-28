import random
import socket
import os
import json

from flask import current_app
from datetime import datetime
from config import load_meta_data

metadata_file = load_meta_data()


# 사용가능한 포트번호 탐색
def find_available_port(start_port, end_port):
    while True:
        trial_port = random.randint(start_port, end_port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            port_is_used = sock.connect_ex(("localhost", trial_port)) == 0
            if not port_is_used:
                return trial_port


# metadata.json 파일에 메타 정보 저장 및 업데이트
def update_metadata_json(filename, framework, extension, input_type, output_type):
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


# metadata.json 파일 메타 정보 읽어오기
def read_metadata_json():
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


# db에 메타 정보 저장 및 업데이트
def update_metadata_db(filename, framework, extension, input_type, output_type):
    model_name = filename.rsplit(".", 1)[0]  # 파일 확장자를 제거하여 모델명을 얻음
    current_date = datetime.now().strftime("%Y-%m-%d")
    metadata = {
        "model_name": model_name,
        "framework": framework,
        "extension": extension,
        "input_type": input_type,
        "output_type": output_type,
        "uploaded_date": current_date,
    }
    result = current_app.db_metadata.insert_one(metadata)
    print("result: ", result.inserted_id)
    return result


# db 메타 정보 읽어오기
def read_metadata_db():
    result = current_app.db_metadata.find()
    print(result)
    return result


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


# db에 모델 정보 저장 및 업데이트
def update_modeldata_db(model_name, framework, input_type, output_type, tag):
    modeldata = {
        "model_name": model_name,
        "tag": tag,
        "framework": framework,
        "input_type": input_type,
        "output_type": output_type,
    }
    result = current_app.db_modeldata.insert_one(modeldata)
    print("result: ", result.inserted_id)
    return result


# db 모델 정보 읽어오기
def read_modeldata_db():
    result = current_app.db_modeldata.find()
    print(result)
    return result
