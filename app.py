import joblib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import MODEL_OUTPUT_PATH

app = Flask(__name__)
logger = get_logger(__name__)

SELECTED_FEATURES = [
    "Alkaline_Phosphotase",
    "Age",
    "Total_Bilirubin",
    "Aspartate_Aminotransferase",
    "Alamine_Aminotransferase",
    "Direct_Bilirubin",
    "Total_Protiens",
]

LOG_TRANSFORM_COLS = [
    "Total_Bilirubin",
    "Direct_Bilirubin",
    "Alkaline_Phosphotase",
    "Alamine_Aminotransferase",
    "Aspartate_Aminotransferase",
]

try:
    model = joblib.load(MODEL_OUTPUT_PATH)
    logger.info(f"Model loaded successfully from {MODEL_OUTPUT_PATH}")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    model = None


def predict(input_data: dict):
    """
    Applies the same preprocessing as the training pipeline:
      1. log1p transform on skewed columns
      2. Select the 7 features in the correct order
      3. Predict with the trained model
    Returns 1 (liver disease) or 0 (healthy).
    """
    df = pd.DataFrame([input_data])

    for col in LOG_TRANSFORM_COLS:
        if col in df.columns:
            df[col] = np.log1p(df[col])

    df = df[SELECTED_FEATURES]

    prediction = model.predict(df)
    return int(prediction[0])


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error  = None

    if request.method == "POST":
        try:
            if model is None:
                raise CustomException("Model could not be loaded. Please check the model file.", Exception())

            input_data = {
                "Age":                        float(request.form["Age"]),
                "Total_Bilirubin":            float(request.form["Total_Bilirubin"]),
                "Direct_Bilirubin":           float(request.form["Direct_Bilirubin"]),
                "Alkaline_Phosphotase":       float(request.form["Alkaline_Phosphotase"]),
                "Alamine_Aminotransferase":   float(request.form["Alamine_Aminotransferase"]),
                "Aspartate_Aminotransferase": float(request.form["Aspartate_Aminotransferase"]),
                "Total_Protiens":             float(request.form["Total_Protiens"]),
            }

            result = predict(input_data)
            logger.info(f"Prediction served successfully: {result}")

        except CustomException as ce:
            error = str(ce)
            logger.error(f"CustomException in /: {error}")

        except Exception as e:
            error = "An unexpected error occurred. Please check your inputs."
            logger.error(f"Unexpected error in /: {e}")

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)