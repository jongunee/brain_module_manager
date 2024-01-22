import bentoml
from bentoml.io import NumpyNdarray, PandasDataFrame, PandasSeries, JSON
from pydantic import BaseModel, create_model

import pandas as pd
import numpy as np
import os
import json
import ast
import yaml


def load_env_variables():
    with open("model_config.yaml") as f:
        config = yaml.full_load(f)

    framework = config["framework"]
    model_name = config["model_name"]
    input_type = config["input_type"]
    output_type = config["output_type"]
    api_data = config["api_data"]
    service_name = model_name.split(":")[0]

    return framework, model_name, input_type, output_type, api_data, service_name


def parse_value(value, type_str):
    if type_str == "int":
        return int(value)
    elif type_str == "float":
        return float(value)
    elif type_str == "bool":
        return value.lower() == "true"
    else:
        return value


# 입력 데이터 프레임 생성 함수
def create_input_dataframe(input_data, input_type_str):
    # print(input_type_str)
    if input_type_str == "JSON":
        # Pydantic 모델 인스턴스를 딕셔너리로 변환
        data_dict = input_data.model_dump()
        return pd.DataFrame([data_dict])
    elif input_type_str == "PandasSeries":
        return input_data.values.reshape(1, -1)
    else:
        return input_data


# Framework에 따른 모델 실행 함수
def execute_model(input_df, framework, model_runner):
    if framework == "sklearn":
        return model_runner.predict.run(input_df)
    elif framework == "keras":
        return model_runner.predict(input_df)
    elif framework == "pytorch":
        input_tensor = torch.from_numpy(input_df.to_numpy())
        with torch.no_grad():
            return model_runner(input_tensor).numpy()
    elif framework == "tensorflow":
        return model_runner(input_df.to_numpy()).numpy()
    else:
        raise NotImplementedError(f"Unsupported framework: '{framework}'")


# 결과를 설정한 output type으로 변환하는 함수
def convert_to_output_type(result, output_type):
    if output_type == "PandasDataFrame":
        if not isinstance(result, pd.DataFrame):
            return pd.DataFrame(result)
        return result
    elif output_type == "PandasSeries":
        if not isinstance(result, pd.Series):
            return pd.Series(result)
        return result
    elif output_type == "NumpyNdarray":
        if isinstance(result, pd.DataFrame):
            return result.to_numpy()
        elif isinstance(result, pd.Series):
            return result.to_numpy()
    return result


# GPU 경고 무시
# os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
# tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)


(
    framework,
    model_name,
    input_type,
    output_type,
    api_data,
    service_name,
) = load_env_variables()

if framework == "keras":
    import tensorflow as tf
elif framework == "pytorch":
    import torch
elif framework == "tensorflow":
    import tensorflow as tf

api_data = json.loads(api_data.replace("'", '"'))
# print("***converted api_data: ", api_data)

np_ndarr_sample = np.array([]).reshape(1, -1)
pd_df_sample = pd.DataFrame()
pd_series_sample = pd.Series()
fields = {}

# print(api_data.items())
for key, value in api_data.items():
    # print("key, values: ", key, value)
    # 필드 처리
    field_name, field_type_str = key.split(":")
    parsed_value = parse_value(value, field_type_str)
    fields[field_name] = (eval(field_type_str), parsed_value)

    # NumPy ndarray에 값 추가
    np_ndarr_sample = np.append(np_ndarr_sample, [[parsed_value]], axis=1)

    # Pandas DataFrame에 값 추가
    pd_df_sample[field_name] = [parsed_value]

    # Pandas Series에 값 추가
    pd_series_sample[field_name] = parsed_value
    # print("pd_series_sample: ", pd_series_sample)


ApiDynamicModel = create_model("ApiDynamicModel", **fields)
# print("DynamicModel", DynamicModel)
api_model_instance = ApiDynamicModel()

# input_spec = JSON.from_sample(model_instance)

# print("**input_spec: ", input_spec)


# Input 컴포넌트 생성성
if input_type == "NumpyNdarray":
    input_adapter = NumpyNdarray.from_sample(np_ndarr_sample)
elif input_type == "PandasDataFrame":
    input_adapter = PandasDataFrame.from_sample(pd_df_sample)
elif input_type == "PandasSeries":
    input_adapter = PandasSeries.from_sample(pd_series_sample)
elif input_type == "JSON":
    input_adapter = JSON.from_sample(api_model_instance)
else:
    raise NotImplementedError(f"Unsupported input type: '{input_type}'")

# Output 컴포넌트 생성성
if output_type == "NumpyNdarray":
    output_adapter = NumpyNdarray()
elif output_type == "PandasDataFrame":
    output_adapter = PandasDataFrame()
elif output_type == "PandasSeries":
    output_adapter = PandasSeries()
elif output_type == "JSON":
    output_adapter = JSON()
else:
    raise NotImplementedError(f"Unsupported output type: '{output_type}'")

# 프레임워크에 따라 적절한 model runner 로드
if framework == "sklearn":
    model_runner = bentoml.sklearn.get(model_name).to_runner()
elif framework == "keras":
    model_runner = bentoml.keras.get(model_name).to_runner()
elif framework == "pytorch":
    model_runner = bentoml.pytorch.get(model_name).to_runner()
elif framework == "tensorflow":
    model_runner = bentoml.tensorflow.get(model_name).to_runner()
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
        # print("input_df: ", input_df)

        # 2. Framework에 따라 모델 실행
        result = execute_model(input_df, framework, model_runner)
        # print("result: ", result)

        # 3. 결과를 설정한 output type으로 변환
        output_data = convert_to_output_type(result, output_type)
        # print("output_data: ", output_data)
        # 성공적인 응답
        if output_type == "JSON":
            response = {
                "success": True,
                "message": "Success",
                "result": output_data.tolist(),
            }
        else:
            response = output_data

    except Exception as e:
        if output_type == "JSON":
            # 에러 발생시 실패 응답
            response = {"success": False, "message": f"Fail: {str(e)}"}
        else:
            response = output_data

    return response
