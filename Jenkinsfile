pipeline {
    agent any

    environment {
        SONAR_PROJECT_KEY = 'liver_disease_mlops'  
        SONAR_SCANNER_HOME = tool 'Sonarqube'
        VENV_DIR = 'venv'
        GCP_PROJECT = 'neat-chain-464913-k3'
        GCLOUD_PATH = "/usr/lib/google-cloud-sdk/bin"
        KUBECTL_AUTH_PLUGIN = "/usr/lib/google-cloud-sdk/bin/gke-gcloud-auth-plugin"
    }

    stages{
        stage("Cloning from Github..."){
            steps{
                script{
                    echo 'Cloning from Github...'
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/htasoftware99/liver_disease_mlops.git']])
                }
            }
        }

        stage('SonarQube Analysis'){
			steps {
				withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
    					
					withSonarQubeEnv('Sonarqube') {
    						sh """
						${SONAR_SCANNER_HOME}/bin/sonar-scanner \
						-Dsonar.projectKey=${SONAR_PROJECT_KEY} \
						-Dsonar.sources=. \
						-Dsonar.host.url=http://sonarqube-dind:9000 \
						-Dsonar.login=${SONAR_TOKEN}
						"""
					}
				}
			}
		}

        stage("Making a virtual environment..."){
            steps{
                script{
                    echo 'Making a virtual environment...'
                    sh '''
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -e .
                    '''
                }
            }
        }

        stage('Build, Scan and Push Image to GCR'){
            steps{
                withCredentials([file(credentialsId:'gcp-key' , variable: 'GOOGLE_APPLICATION_CREDENTIALS' )]){
                    script{
                        echo 'Building, scanning and pushing image to GCR...'
                        sh '''
                        export PATH=$PATH:${GCLOUD_PATH}
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${GCP_PROJECT}
                        gcloud auth configure-docker --quiet
                        
                        # 1. build the Docker image
                        docker build -t gcr.io/${GCP_PROJECT}/liver-disease-mlops:latest .
                        
                        # 2. Scan the image with Trivy, allowing the build to proceed even if vulnerabilities are found
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy:0.62.1 image --severity HIGH,CRITICAL gcr.io/${GCP_PROJECT}/liver-disease-mlops:latest || true
                        
                        # 3. Scan successful, push the image to GCP
                        docker push gcr.io/${GCP_PROJECT}/liver-disease-mlops:latest
                        '''
                    }
                }
            }
        }

        stage('Deploying to Kubernetes'){
            steps{
                withCredentials([file(credentialsId:'gcp-key' , variable: 'GOOGLE_APPLICATION_CREDENTIALS' )]){
                    script{
                        echo 'Deploying to Kubernetes'
                        sh '''
                        export PATH=$PATH:${GCLOUD_PATH}:${KUBECTL_AUTH_PLUGIN}
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${GCP_PROJECT}
                        gcloud container clusters get-credentials ml-app-cluster --zone us-central1-a
                        kubectl apply -f deployment.yml
                        '''
                    }
                }
            }
        }
    }
}