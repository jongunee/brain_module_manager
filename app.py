from flask import Flask, render_template, request
import socket
import subprocess
import os
import json
import tempfile
import random

app = Flask(__name__)

# 저장된 학습 모델 리스트 찾기


def get_saved_models(base_models_dir):
  all_model_info = []
  for model_name in os.listdir(base_models_dir):
    model_base_dir = os.path.join(base_models_dir, model_name)
    if os.path.isdir(model_base_dir):
      for tag_name in os.listdir(model_base_dir):
        sub_model_dir = os.path.join(model_base_dir, tag_name)
        if os.path.isdir(sub_model_dir):
          all_model_info.append(
              (model_name, tag_name, "", "", ""))
  return all_model_info


base_models_dir = r'C:\Users\whsrj\bentoml\models'
saved_models = get_saved_models(base_models_dir)

# 현재 사용가능한 포트를 찾아 사용가능한 랜덤 포트 찾기

server_info = {}


def find_available_port(start_port, end_port):
  while True:
    trial_port = random.randint(start_port, end_port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      port_is_used = sock.connect_ex(('localhost', trial_port)) == 0
      if not port_is_used:
        return trial_port


@app.route('/')
def home():
  return render_template('index.html')


@app.route('/models')
def models():
  return render_template('model_list.html', saved_models=saved_models)


@app.route('/servers')
def servers():
  return render_template('server_list.html', server_info=server_info)


@app.route('/service', methods=['POST'])
def service():
  serve_file = 'service'
  port = find_available_port(2000, 3000)
  ip = '127.0.0.1'

  # body에 포함된 데이터를 'config_data'로 받기
  config_data = request.json
  # print("Received config_data:", config_data)

  # 임시 파일 생성
  config_file = tempfile.NamedTemporaryFile(delete=False)
  config_file.write(json.dumps(config_data).encode('utf-8'))
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

  model_name = config_data['model_name']

  if model_name not in server_info:
    server_info[model_name] = []

  server_info[model_name].append(
      {'config_data': config_data, 'ip': ip, 'port': port})
  print(server_info)

  return f"Started service: {serve_file} on port {port}"


@app.route('/info', methods=['GET'])
def info():
  return server_info


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
