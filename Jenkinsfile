pipeline {
    agent any

    environment {
        PROJECT_NAME = 'fastapi-service'
        PYTHON_VERSION = '3.11'
        VENV_PATH = "${WORKSPACE}/venv"
        ENVIRONMENT = 'production'
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    // JSON 로그 출력
                    sh '''
                        chmod +x jenkins-logger.sh
                        ./jenkins-logger.sh INFO "Starting source code checkout"
                    '''
                    checkout scm
                    sh './jenkins-logger.sh INFO "Source code checkout completed"'
                }
            }
        }

        stage('Setup Python Environment') {
            steps {
                script {
                    sh './jenkins-logger.sh INFO "Setting up Python virtual environment"'
                    sh '''
                        python3 -m venv ${VENV_PATH}
                        . ${VENV_PATH}/bin/activate
                        pip install --upgrade pip
                    '''
                    sh './jenkins-logger.sh INFO "Python environment setup completed"'
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    sh './jenkins-logger.sh INFO "Installing dependencies from requirements.txt"'
                    def result = sh(script: '''
                        . ${VENV_PATH}/bin/activate
                        pip install -r requirements.txt 2>&1
                    ''', returnStatus: true)

                    if (result != 0) {
                        sh './jenkins-logger.sh ERROR "Failed to install dependencies"'
                        error("Dependency installation failed")
                    }
                    sh './jenkins-logger.sh INFO "Dependencies installed successfully"'
                }
            }
        }

        stage('Lint') {
            steps {
                script {
                    sh './jenkins-logger.sh INFO "Running code linting checks"'
                    sh '''
                        . ${VENV_PATH}/bin/activate
                        pip install flake8 pylint || true
                        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
                    '''
                    sh './jenkins-logger.sh INFO "Linting checks completed"'
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    sh './jenkins-logger.sh INFO "Running test suite"'
                    def testResult = sh(script: '''
                        . ${VENV_PATH}/bin/activate
                        pip install pytest pytest-cov || true
                        pytest --verbose --cov=. --cov-report=xml --cov-report=html 2>&1
                    ''', returnStatus: true)

                    if (testResult != 0) {
                        sh './jenkins-logger.sh WARN "Some tests failed or no tests found"'
                    } else {
                        sh './jenkins-logger.sh INFO "All tests passed successfully"'
                    }
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    sh './jenkins-logger.sh INFO "Building application"'
                    def buildResult = sh(script: '''
                        . ${VENV_PATH}/bin/activate
                        python -m compileall . 2>&1
                    ''', returnStatus: true)

                    if (buildResult != 0) {
                        sh './jenkins-logger.sh ERROR "Application build failed"'
                        error("Build failed")
                    }
                    sh './jenkins-logger.sh INFO "Application build completed successfully"'
                }
            }
        }

        stage('Health Check') {
            steps {
                script {
                    sh './jenkins-logger.sh INFO "Running health check"'
                    def healthResult = sh(script: '''
                        . ${VENV_PATH}/bin/activate
                        python -c "import main; print('Import successful')" 2>&1
                    ''', returnStatus: true)

                    if (healthResult != 0) {
                        sh './jenkins-logger.sh ERROR "Health check failed - import error detected"'
                        error("Health check failed")
                    }
                    sh './jenkins-logger.sh INFO "Health check passed"'
                }
            }
        }
    }

    post {
        success {
            script {
                sh './jenkins-logger.sh INFO "Build completed successfully"'
                // Webhook to DevOps API
                sh '''
                    curl -X POST http://host.docker.internal:8000/webhook/jenkins \
                      -H "Content-Type: application/json" \
                      -d '{
                        "service": "fastapi-service",
                        "status": "success",
                        "build_number": "'${BUILD_NUMBER}'",
                        "git_repo": "'${GIT_URL}'",
                        "git_branch": "'${GIT_BRANCH}'",
                        "job_name": "'${JOB_NAME}'"
                      }' || true
                '''
            }
        }
        failure {
            script {
                sh './jenkins-logger.sh ERROR "Build failed - triggering failure webhook"'
                // Webhook to DevOps API with error details
                sh '''
                    curl -X POST http://host.docker.internal:8000/webhook/jenkins \
                      -H "Content-Type: application/json" \
                      -d '{
                        "service": "fastapi-service",
                        "status": "failure",
                        "build_number": "'${BUILD_NUMBER}'",
                        "git_repo": "'${GIT_URL}'",
                        "git_branch": "'${GIT_BRANCH}'",
                        "job_name": "'${JOB_NAME}'"
                      }' || true
                '''
            }
        }
        always {
            script {
                sh './jenkins-logger.sh INFO "Build finished - cleaning workspace"'
                cleanWs()
            }
        }
    }
}
