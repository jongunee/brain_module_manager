from flask import Flask, render_template, request
import subprocess
import os
import json
import tempfile

app = Flask(__name__)


def get_saved_models(base_models_dir):
  all_model_info = []
  for model_name in os.listdir(base_models_dir):
    model_base_dir = os.path.join(base_models_dir, model_name)
    if os.path.isdir(model_base_dir):
      for tag_name in os.listdir(model_base_dir):
        sub_model_dir = os.path.join(model_base_dir, tag_name)
        if os.path.isdir(sub_model_dir):
          # Add sample model details such as input type, output type, and framework.
          all_model_info.append(
              (model_name, tag_name, "", "", ""))
  return all_model_info


base_models_dir = r'C:\Users\whsrj\bentoml\models'
saved_models = get_saved_models(base_models_dir)


@app.route('/models')
def list_models():
  return render_template('model_list.html', saved_models=saved_models)


@app.route('/service', methods=['POST'])
def service():
  service_name = 'service'
  port = 1995

  # 'config' 받기 및 전달
  config_data = request.json
  print("Received config_data:", config_data)  # 받은 config_data 로깅

  config_file = tempfile.NamedTemporaryFile(delete=False)
  config_file.write(json.dumps(config_data).encode('utf-8'))
  config_file.close()

  cmd = f"bentoml serve {service_name}:svc --host 0.0.0.0 --port {port} --reload"

  # 서브 프로세스를 실행하고 백그라운드에서 실행됩니다.
  with tempfile.NamedTemporaryFile(delete=False) as config_file:
    config_filepath = config_file.name
    with open(config_filepath, "w") as f:
      json.dump(config_data, f)
    env_vars = os.environ.copy()
    env_vars["CONFIG_PATH"] = config_filepath
    subprocess.Popen(cmd.split(), env=env_vars)

  return f"Started service: {service_name} on port {port}"


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
