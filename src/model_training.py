import os
import time
import joblib
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from torch.utils.tensorboard import SummaryWriter
from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *
from utils.common_functions import load_data, read_yaml

logger = get_logger(__name__)

EXTRA_TREES_PARAMS = {
    "n_estimators": [100, 200, 300],
    "max_depth": [None, 10, 20, 30],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
    "criterion": ["gini", "entropy"]
}

GRID_SEARCH_PARAMS = {
    "cv": 5,
    "n_jobs": -1,
    "verbose": 1,
    "scoring": "accuracy",
}

class ModelTraining:

    def __init__(self, train_path, test_path, model_output_path, target_col="Dataset"):
        self.train_path = train_path
        self.test_path = test_path
        self.model_output_path = model_output_path
        self.target_col = target_col

        # --- TensorBoard Setup ---
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.log_dir = f"tensorboard_logs/run_{timestamp}"
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.writer = SummaryWriter(log_dir=self.log_dir)
        logger.info(f"ModelTraining initialized. TensorBoard logs will be saved to {self.log_dir}")

    def load_and_split_data(self):
        try:
            logger.info(f"Loading train data from {self.train_path}")
            train_df = load_data(self.train_path)

            logger.info(f"Loading test data from {self.test_path}")
            test_df = load_data(self.test_path)

            X_train = train_df.drop(columns=[self.target_col])
            y_train = train_df[self.target_col]

            X_test = test_df.drop(columns=[self.target_col])
            y_test = test_df[self.target_col]

            logger.info("Data loaded and split into X and y successfully.")
            return X_train, y_train, X_test, y_test

        except Exception as e:
            logger.error(f"Error while loading and splitting data: {e}")
            raise CustomException("Failed to load and split data", e)

    def train_model(self, X_train, y_train):
        try:
            logger.info("Initializing Extra Trees model.")
            et_model = ExtraTreesClassifier(random_state=42)

            logger.info("Starting hyperparameter tuning with GridSearchCV.")
            grid_search = GridSearchCV(
                estimator=et_model,
                param_grid=EXTRA_TREES_PARAMS,
                cv=GRID_SEARCH_PARAMS["cv"],
                n_jobs=GRID_SEARCH_PARAMS["n_jobs"],
                verbose=GRID_SEARCH_PARAMS["verbose"],
                scoring=GRID_SEARCH_PARAMS["scoring"],
            )

            grid_search.fit(X_train, y_train)

            best_params = grid_search.best_params_
            best_model = grid_search.best_estimator_

            logger.info(f"Best parameters found: {best_params}")
            logger.info(f"Best CV score: {grid_search.best_score_:.4f}")

            # Log best hyperparameters to TensorBoard as text
            param_str = "  \n".join([f"**{k}**: {v}" for k, v in best_params.items()])
            self.writer.add_text("Model/Best_Hyperparameters", param_str, global_step=0)
            self.writer.add_scalar("CV/Best_Score", grid_search.best_score_, global_step=0)

            return best_model, best_params

        except Exception as e:
            logger.error(f"Error while training the model: {e}")
            raise CustomException("Failed to train Extra Trees model", e)

    def evaluate_model(self, model, X_test, y_test):
        try:
            logger.info("Evaluating model on the test set.")

            y_pred = model.predict(X_test)

            accuracy  = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall    = recall_score(y_test, y_pred)
            f1        = f1_score(y_test, y_pred)

            logger.info(f"Accuracy  : {accuracy:.4f}")
            logger.info(f"Precision : {precision:.4f}")
            logger.info(f"Recall    : {recall:.4f}")
            logger.info(f"F1 Score  : {f1:.4f}")

            metrics = {
                "accuracy":  accuracy,
                "precision": precision,
                "recall":    recall,
                "f1":        f1,
            }

            # Log metrics to TensorBoard
            self.writer.add_scalar("Test_Metrics/Accuracy", accuracy, global_step=0)
            self.writer.add_scalar("Test_Metrics/Precision", precision, global_step=0)
            self.writer.add_scalar("Test_Metrics/Recall", recall, global_step=0)
            self.writer.add_scalar("Test_Metrics/F1_Score", f1, global_step=0)

            return metrics

        except Exception as e:
            logger.error(f"Error while evaluating the model: {e}")
            raise CustomException("Failed to evaluate model", e)

    def save_model(self, model):
        try:
            os.makedirs(os.path.dirname(self.model_output_path), exist_ok=True)
            joblib.dump(model, self.model_output_path)
            logger.info(f"Model successfully saved to {self.model_output_path}")

        except Exception as e:
            logger.error(f"Error while saving the model: {e}")
            raise CustomException("Failed to save model", e)

    def run(self):
        try:
            logger.info("=" * 50)
            logger.info("Starting Model Training pipeline...")

            X_train, y_train, X_test, y_test = self.load_and_split_data()
            
            best_model, best_params = self.train_model(X_train, y_train)

            metrics = self.evaluate_model(best_model, X_test, y_test)

            self.save_model(best_model)

            logger.info("Model Training pipeline completed successfully.")
            logger.info("=" * 50)

        except CustomException as ce:
            logger.error(f"CustomException: {str(ce)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Model Training pipeline: {e}")
            raise CustomException("Failed during Model Training pipeline", e)
        finally:
            # Ensure TensorBoard writer is flushed and closed
            self.writer.flush()
            self.writer.close()
            logger.info("TensorBoard writer closed.")


if __name__ == "__main__":
    try:
        config = read_yaml(CONFIG_PATH)
        target_col = config.get("data_processing", {}).get("target_column", "Dataset")
    except Exception:
        target_col = "Dataset"

    trainer = ModelTraining(
        train_path=PROCESSED_TRAIN_DATA_PATH,
        test_path=PROCESSED_TEST_DATA_PATH,
        model_output_path=MODEL_OUTPUT_PATH,
        target_col=target_col
    )
    trainer.run()