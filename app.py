import os
from flask import Flask, render_template

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


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
