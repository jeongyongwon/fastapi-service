#!/bin/bash
# =======================================================
# Jenkins JSON 로그 출력 유틸리티
# Application 로그 포맷과 동일한 JSON 형식으로 출력
# =======================================================

# 환경 변수 기본값 설정
SERVICE_NAME="${PROJECT_NAME:-unknown-service}"
ENVIRONMENT="${ENVIRONMENT:-production}"
HOST_NAME="${HOSTNAME:-$(hostname)}"
JOB_NAME="${JOB_NAME:-unknown-job}"
BUILD_NUMBER="${BUILD_NUMBER:-0}"
GIT_REPO="${GIT_URL:-unknown}"
GIT_BRANCH="${GIT_BRANCH:-unknown}"

# JSON 로그 출력 함수
log_json() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")

    # JSON 객체 생성 (application 로그 포맷과 통일)
    cat <<EOF
{"timestamp":"${timestamp}","level":"${level}","service":"${SERVICE_NAME}","environment":"${ENVIRONMENT}","host":"${HOST_NAME}","message":"${message}","component":"jenkins","job_name":"${JOB_NAME}","build_number":"${BUILD_NUMBER}","git_repo":"${GIT_REPO}","git_branch":"${GIT_BRANCH}"}
EOF
}

# 사용법에 따라 함수 제공
log_info() {
    log_json "INFO" "$1"
}

log_warn() {
    log_json "WARN" "$1"
}

log_error() {
    log_json "ERROR" "$1"
}

log_debug() {
    log_json "DEBUG" "$1"
}

# 직접 호출 시 (./jenkins-logger.sh LEVEL "message")
if [ "$#" -ge 2 ]; then
    log_json "$1" "$2"
fi
