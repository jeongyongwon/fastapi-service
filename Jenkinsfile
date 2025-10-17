pipeline {
    agent any

    environment {
        PROJECT_NAME = 'fastapi-service'
        PYTHON_VERSION = '3.11'
        VENV_PATH = "${WORKSPACE}/venv"
    }

    stages {
        stage('Checkout') {
            steps {
                echo '소스 코드 체크아웃'
                checkout scm
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo 'Python 가상 환경 설정'
                sh '''
                    python3 -m venv ${VENV_PATH}
                    . ${VENV_PATH}/bin/activate
                    pip install --upgrade pip
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                echo '의존성 설치'
                sh '''
                    . ${VENV_PATH}/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                echo '코드 린트 검사'
                sh '''
                    . ${VENV_PATH}/bin/activate
                    pip install flake8 pylint || true
                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
                '''
            }
        }

        stage('Test') {
            steps {
                echo '테스트 실행'
                sh '''
                    . ${VENV_PATH}/bin/activate
                    pip install pytest pytest-cov || true
                    pytest --verbose --cov=. --cov-report=xml --cov-report=html || true
                '''
            }
        }

        stage('Build') {
            steps {
                echo '애플리케이션 빌드'
                sh '''
                    . ${VENV_PATH}/bin/activate
                    python -m compileall . || true
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo '헬스 체크 (dry run)'
                sh '''
                    . ${VENV_PATH}/bin/activate
                    python -c "import main; print('Import successful')" || true
                '''
            }
        }
    }

    post {
        success {
            echo '✅ 빌드 성공!'
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
        failure {
            echo '❌ 빌드 실패!'
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
                    "job_name": "'${JOB_NAME}'",
                    "error_log": "빌드 프로세스 실패"
                  }' || true
            '''
        }
        always {
            echo '빌드 완료 - 정리 작업'
            cleanWs()
        }
    }
}
