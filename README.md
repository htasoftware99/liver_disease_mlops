# Liver Disease Prediction MLOps Project

This project implements an end-to-end MLOps pipeline for predicting liver disease based on patient records. It covers the entire machine learning lifecycle, from data ingestion and processing to model training, evaluation, and deployment on Google Kubernetes Engine (GKE).

## 🏗️ System Architecture

<p align="center">
  <img src="structure.png" width="700"/>
</p>

## 🚀 Project Overview

The goal of this project is to build a robust and scalable system that can predict whether a patient has liver disease using biochemical markers. The project emphasizes MLOps principles, including data versioning, infrastructure as code (IaC), automated CI/CD pipelines, and experiment tracking.

## 🛠️ Tech Stack

- **Programming Language:** Python 3.x
- **Machine Learning:** Scikit-learn, XGBoost, Imbalanced-learn (SMOTE)
- **Data Versioning:** DVC (Data Version Control)
- **Infrastructure:** Terraform, Google Cloud Platform (GCS, GKE)
- **Deployment:** Docker, Kubernetes (GKE), Flask
- **CI/CD:** Jenkins, SonarQube (Code Quality), Trivy (Container Security)
- **Experiment Tracking:** TensorBoard

## 📁 Project Structure

```text
├── .dvc/                   # DVC configuration and cache
├── config/                 # YAML configuration and path management
├── infrastructure/         # Terraform files for GCP/GKE
├── src/                    # Source code for the ML pipeline
│   ├── data_ingestion.py   # Fetching data from GCS
│   ├── data_processing.py  # Cleaning, SMOTE, and Feature Selection
│   ├── model_training.py   # Training with GridSearchCV and TensorBoard
│   ├── logger.py           # Custom logging setup
│   └── custom_exception.py # Custom exception handling
├── static/                 # CSS files for the web app
├── templates/              # HTML templates for the web app
├── app.py                  # Flask web application
├── dvc.yaml                # DVC pipeline definition
├── Jenkinsfile             # Jenkins CI/CD pipeline
├── Dockerfile              # Docker image definition
└── deployment.yml          # Kubernetes deployment configuration
```

## ⚙️ Pipeline Details

### 1. Data Ingestion
Data is fetched from a Google Cloud Storage bucket. The pipeline is designed to be reproducible using DVC.

### 2. Data Processing
- **Missing Value Imputation:** Medians are calculated from the training set and applied to both train and test sets to prevent data leakage.
- **Outlier Handling:** IQR-based clipping/filtering.
- **Skewness Correction:** `log1p` transformation for highly skewed numerical features.
- **Class Balancing:** SMOTE (Synthetic Minority Over-sampling Technique) is applied to the training data.
- **Feature Selection:** `ExtraTreesClassifier` is used to identify and select the top 7 most impactful features.

### 3. Model Training
- **Algorithm:** `ExtraTreesClassifier`.
- **Optimization:** `GridSearchCV` for hyperparameter tuning.
- **Tracking:** Metrics (Accuracy, Precision, Recall, F1) and hyperparameters are logged to **TensorBoard**.

### 4. Deployment
- **Web App:** A Flask-based interface allows users to input patient data and receive predictions in real-time.
- **Containerization:** The application is containerized using Docker.
- **Orchestration:** Deployed on Google Kubernetes Engine (GKE) for high availability and scaling.

### 5. CI/CD Pipeline (Jenkins)
The project includes a fully automated Jenkins pipeline that manages the lifecycle of the application:
- **SonarQube Analysis:** Scans the source code for bugs, vulnerabilities, and code smells.
- **Trivy Scanning:** Scans the Docker image for security vulnerabilities (HIGH/CRITICAL) before deployment.
- **GCR & GKE Integration:** Automatically builds, pushes images to Google Container Registry, and deploys to the GKE cluster.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Docker
- Google Cloud SDK (configured)
- Terraform

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd liver-disease-mlops
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize DVC:**
   ```bash
   dvc init
   ```

### Running the Application Locally

1. **Run the training pipeline:**
   ```bash
   python src/data_ingestion.py
   python src/data_processing.py
   python src/model_training.py
   ```
   or

   ```bash
   dvc repro
   ```

2. **Start the Flask app:**
   ```bash
   python app.py
   ```
   Access the app at `http://localhost:5000`.

## ☁️ Infrastructure & Deployment

### Terraform (IaC)
Navigate to the `infrastructure/` directory to provision GCP resources:
```bash
terraform init
terraform plan
terraform apply
```

### Jenkins
Deploy to GKE:
Click build now on Jenkins pipeline

## 📈 Monitoring
To view experiment logs in TensorBoard:
```bash
tensorboard --logdir tensorboard_logs
```
### Terraform Destroy (IaC)
Navigate to the `infrastructure/` directory to provision GCP resources:
```bash
terraform destroy
```