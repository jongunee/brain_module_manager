import bentoml
from bentoml.io import NumpyNdarray, PandasDataFrame, PandasSeries, JSON

import pandas as pd
import numpy as np
import os
import json

from tensorflow.python.keras.models import load_model
import tensorflow as tf
import torch

# GPU 경고 무시
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

# conig 파일 로드
config_filepath = os.environ.get('CONFIG_PATH')

if config_filepath:
  with open(config_filepath, 'r') as f:
    config = json.load(f)

# config 설정 로드
framework = config['framework']
model_name = config['model_name']
input_type = config['input_type']
output_type = config['output_type']
service_name = model_name.split(':')[0]

# Input 컴포넌트 생성성
if input_type == 'NumpyNdarray':
  input_adapter = NumpyNdarray()
elif input_type == 'PandasDataFrame':
  input_adapter = PandasDataFrame()
elif input_type == 'PandasSeries':
  input_adapter = PandasSeries()
elif input_type == 'JSON':
  input_adapter = JSON()
else:
  raise NotImplementedError(f"Unsupported input type: '{input_type}'")

# Output 컴포넌트 생성성
if output_type == 'NumpyNdarray':
  output_adapter = NumpyNdarray()
elif output_type == 'PandasDataFrame':
  output_adapter = PandasDataFrame()
elif output_type == 'PandasSeries':
  output_adapter = PandasSeries()
elif output_type == 'JSON':
  output_adapter = JSON()
else:
  raise NotImplementedError(f"Unsupported output type: '{output_type}'")

# 프레임워크에 따라 적절한 model runner 로드
if framework == 'sklearn':
  model_runner = bentoml.sklearn.get(model_name).to_runner()
elif framework == 'keras':
  model_runner = load_model(model_name)
elif framework == 'pytorch':
  model_runner = torch.load(model_name)
elif framework == 'tensorflow':
  model_runner = tf.saved_model.load(model_name)
else:
  raise NotImplementedError(f"Unsupported framework: '{framework}'")
# BentoML service 생성
svc = bentoml.Service(service_name, runners=[model_runner])

# API 정의


@svc.api(input=input_adapter, output=output_adapter)
def predict(input_data):
  try:
    # 1. 입력 데이터 프레임 생성
    input_df = create_input_dataframe(input_data, input_type)

    # 2. Framework에 따라 모델 실행
    result = execute_model(input_df, framework, model_runner)

    # 3. 결과를 설정한 output type으로 변환
    output_data = convert_to_output_type(result, input_type)

    # 성공적인 응답
    if output_type == 'JSON':
      response = {
          'success': True,
          'message': 'Success',
          'result': output_data.tolist()
      }
    else:
      response = output_data

  except Exception as e:
    if output_type == 'JSON':
      # 에러 발생시 실패 응답
      response = {
          'success': False,
          'message': f"Fail: {str(e)}"
      }
    else:
      response = output_data

  return response


# 입력 데이터 프레임 생성 함수
def create_input_dataframe(input_data, input_type_str):
  if input_type == 'JSON' or input_type == 'PandasSeries':
    return pd.DataFrame([input_data])
  else:
    return input_data

# Framework에 따른 모델 실행 함수


def execute_model(input_df, framework, model_runner):
  if framework == 'sklearn':
    return model_runner.predict.run(input_df)
  elif framework == 'keras':
    return model_runner.predict(input_df)
  elif framework == 'pytorch':
    input_tensor = torch.from_numpy(input_df.to_numpy())
    with torch.no_grad():
      return model_runner(input_tensor).numpy()
  elif framework == 'tensorflow':
    return model_runner(input_df.to_numpy()).numpy()
  else:
    raise NotImplementedError(f"Unsupported framework: '{framework}'")


# 결과를 설정한 output type으로 변환하는 함수
def convert_to_output_type(result, output_type):
  if output_type == 'PandasDataFrame':
    if not isinstance(result, pd.DataFrame):
      return pd.DataFrame(result)
    return result
  elif output_type == 'PandasSeries':
    if not isinstance(result, pd.Series):
      return pd.Series(result)
    return result
  elif output_type == 'NumpyNdarray':
    if isinstance(result, pd.DataFrame):
      return result.to_numpy()
    elif isinstance(result, pd.Series):
      return result.to_numpy()
  return result


# service 실행
if __name__ == '__main__':
  svc.run()
