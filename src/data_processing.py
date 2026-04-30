import os
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE

from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *
from utils.common_functions import read_yaml, load_data

logger = get_logger(__name__)

class DataProcessor:

    def __init__(self, train_path, test_path, processed_dir, config_path):
        self.train_path    = train_path
        self.test_path     = test_path
        self.processed_dir = processed_dir

        self.config    = read_yaml(config_path)
        self.dp_config = self.config["data_processing"]

        self.target_col    = self.dp_config["target_column"]
        self.cat_cols      = self.dp_config["categorical_columns"]
        self.num_cols      = self.dp_config["numerical_columns"]
        self.iqr_mult      = self.dp_config["outlier_iqr_multiplier"]
        self.skew_thresh   = self.dp_config["skewness_threshold"]
        self.n_features    = self.dp_config["no_of_features"]

        os.makedirs(self.processed_dir, exist_ok=True)
        
        self.impute_values = {}
        self.label_encoders = {}
        self.iqr_bounds = {}
        self.skewed_cols = []
        
        logger.info("DataProcessor initialized (Data Leakage prevented structure).")

    # ------------------------------------------------------------------
    # 1. PREPROCESS TRAIN
    # ------------------------------------------------------------------
    def preprocess_train(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            logger.info("Preprocessing TRAIN data (Fit & Transform)...")

            if "Unnamed: 0" in df.columns:
                df.drop(columns=["Unnamed: 0"], inplace=True)
            df.drop_duplicates(inplace=True)
            df[self.target_col] = df[self.target_col].map({1: 1, 2: 0})

            for col in df.columns:
                if df[col].isnull().sum() > 0:
                    median_val = df[col].median()
                    self.impute_values[col] = median_val
                    df[col].fillna(median_val, inplace=True)
                    logger.info(f"Train - '{col}' filled with median: {median_val}")

            for col in self.cat_cols:
                if col in df.columns:
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col])
                    self.label_encoders[col] = le

            for col in self.num_cols:
                if col in df.columns:
                    Q1  = df[col].quantile(0.25)
                    Q3  = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower = Q1 - self.iqr_mult * IQR
                    upper = Q3 + self.iqr_mult * IQR
                    
                    self.iqr_bounds[col] = (lower, upper) 
                    
                    df = df[(df[col] >= lower) & (df[col] <= upper)]

            skewness = df[self.num_cols].apply(lambda x: x.skew())
            self.skewed_cols = skewness[skewness > self.skew_thresh].index.tolist()
            
            for col in self.skewed_cols:
                df[col] = np.log1p(df[col])
                
            logger.info(f"Train preprocessing completed. Shape: {df.shape}")
            return df

        except Exception as e:
            logger.error(f"Train Preprocess failed: {e}")
            raise CustomException("Train data preprocessing failed.", e)

    # ------------------------------------------------------------------
    # 2. PREPROCESS TEST
    # ------------------------------------------------------------------
    def preprocess_test(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            logger.info("Preprocessing TEST data (Transform Only)...")

            if "Unnamed: 0" in df.columns:
                df.drop(columns=["Unnamed: 0"], inplace=True)
            df[self.target_col] = df[self.target_col].map({1: 1, 2: 0})

            for col, median_val in self.impute_values.items():
                if col in df.columns:
                    df[col].fillna(median_val, inplace=True)
            df.fillna(0, inplace=True)

            for col, le in self.label_encoders.items():
                if col in df.columns:
                    classes_dict = {c: i for i, c in enumerate(le.classes_)}
                    df[col] = df[col].map(classes_dict).fillna(-1).astype(int)

            for col, (lower, upper) in self.iqr_bounds.items():
                if col in df.columns:
                    df[col] = np.clip(df[col], lower, upper)

            for col in self.skewed_cols:
                if col in df.columns:
                    df[col] = np.log1p(df[col])

            logger.info(f"Test preprocessing completed. Shape: {df.shape}")
            return df

        except Exception as e:
            logger.error(f"Test Preprocess failed: {e}")
            raise CustomException("Test data preprocessing failed.", e)

    # ------------------------------------------------------------------
    # 3. BALANCE (SMOTE)
    # ------------------------------------------------------------------
    def balance_data(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            logger.info("Balancing TRAIN data with SMOTE.")
            X = df.drop(columns=[self.target_col])
            y = df[self.target_col]

            smote = SMOTE(random_state=42)
            X_resampled, y_resampled = smote.fit_resample(X, y)

            balanced_df = pd.DataFrame(X_resampled, columns=X.columns)
            balanced_df[self.target_col] = y_resampled

            return balanced_df

        except Exception as e:
            logger.error(f"Data balancing step failed: {e}")
            raise CustomException("Data balancing failed.", e)

    # ------------------------------------------------------------------
    # 4. FEATURE SELECTION
    # ------------------------------------------------------------------
    def select_features(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            logger.info("Feature selection running on TRAIN data.")
            X = df.drop(columns=[self.target_col])
            y = df[self.target_col]

            model = ExtraTreesClassifier(n_estimators=200, random_state=42)
            model.fit(X, y)

            importance_df = pd.DataFrame({
                "feature":    X.columns,
                "importance": model.feature_importances_
            }).sort_values("importance", ascending=False)

            top_features = importance_df["feature"].head(self.n_features).tolist()
            logger.info(f"Selected {self.n_features} features: {top_features}")

            return df[top_features + [self.target_col]], top_features

        except Exception as e:
            logger.error(f"Feature selection step failed: {e}")
            raise CustomException("Feature selection failed.", e)

    # ------------------------------------------------------------------
    # 5. SAVE
    # ------------------------------------------------------------------
    def save_data(self, df: pd.DataFrame, file_path: str) -> None:
        try:
            df.to_csv(file_path, index=False)
            logger.info(f"Data saved → {file_path} (shape: {df.shape})")
        except Exception as e:
            logger.error(f"Error occurred while saving data: {e}")
            raise CustomException("Error occurred while saving data.", e)

    # ------------------------------------------------------------------
    # 6. MAIN PIPELINE
    # ------------------------------------------------------------------
    def process(self) -> None:
        try:
            logger.info("=" * 50)
            logger.info("Data Processing pipeline initializing...")

            train_df = load_data(self.train_path)
            test_df  = load_data(self.test_path)
            logger.info(f"Initial Train shape: {train_df.shape} | Test shape: {test_df.shape}")

            train_df = self.preprocess_train(train_df)
            test_df  = self.preprocess_test(test_df)

            train_df = self.balance_data(train_df)

            train_df, selected_features = self.select_features(train_df)
            test_df = test_df[selected_features + [self.target_col]]

            self.save_data(train_df, PROCESSED_TRAIN_DATA_PATH)
            self.save_data(test_df,  PROCESSED_TEST_DATA_PATH)

            logger.info("Data Processing pipeline successfully completed.")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Data Processing pipeline error: {e}")
            raise CustomException("Data Processing pipeline error occured.", e)


if __name__ == "__main__":
    processor = DataProcessor(
        train_path    = TRAIN_FILE_PATH,
        test_path     = TEST_FILE_PATH,
        processed_dir = PROCESSED_DIR,
        config_path   = CONFIG_PATH
    )
    processor.process()