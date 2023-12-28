import bentoml
import torch
import keras
import joblib
import os
import tensorflow as tf

from . import utils


def save_with_bento(file_path, framework, model_name, input_type, output_type):
    root, extension = os.path.splitext(file_path)
    print(extension)
    result = None

    if framework == "sklearn":
        model = joblib.load(file_path)
        result = bentoml.sklearn.save_model(model_name, model)
    elif framework == "keras":
        model = keras.models.load_model(file_path)
        result = bentoml.keras.save_model(model_name, model)
    elif framework == "tensorflow":
        if extension == ".h5":
            model = keras.models.load_model(file_path)
        else:
            model = tf.saved_model.load(file_path)
        result = bentoml.tensorflow.save_model(model_name, model)
    elif framework == "pytorch":
        model = torch.load(file_path)
        result = bentoml.pytorch.save_model(model_name, model)
    else:
        return "Unsupported framework: {}".format(framework)
    if result:
        tag = str(result.tag).split(":")[1]
        utils.update_modeldata_db(model_name, framework, input_type, output_type, tag)
        return result
