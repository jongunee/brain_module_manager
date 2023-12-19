import bentoml
import torch
import keras
import joblib
import os
import tensorflow as tf


def save_with_bento(framework, file_path, bento_model_name):
    root, extension = os.path.splitext(file_path)
    print(extension)
    if framework == "sklearn":
        model = joblib.load(file_path)
        result = bentoml.sklearn.save_model(bento_model_name, model)
        print("tag:", result.tag)
        return result
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
