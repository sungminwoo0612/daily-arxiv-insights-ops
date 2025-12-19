#!/bin/bash
# 모든 Docker Compose 프로젝트를 중지하는 스크립트

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 에러 핸들링
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

# 함수: 모든 compose 프로젝트 중지
stop_all_compose() {
    local dry_run="${1:-false}"
    
    echo -e "${YELLOW}=== Docker Compose 프로젝트 중지 ===${NC}"
    echo ""
    
    # 실행 중인 프로젝트 목록 가져오기
    local projects
    projects=$(docker compose ls --format json 2>/dev/null | jq -r '.[] | select(.Status | contains("running") or contains("restarting")) | .Name' || echo "")
    
    if [ -z "$projects" ]; then
        echo -e "${GREEN}실행 중인 Docker Compose 프로젝트가 없습니다.${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}중지할 프로젝트 목록:${NC}"
    echo "$projects" | while read -r project; do
        if [ -n "$project" ]; then
            echo "  - $project"
        fi
    done
    echo ""
    
    if [ "$dry_run" = "true" ]; then
        echo -e "${YELLOW}[DRY RUN] 다음 프로젝트들이 중지될 예정입니다:${NC}"
        echo "$projects" | while read -r project; do
            if [ -n "$project" ]; then
                local config_file
                config_file=$(docker compose ls --format json 2>/dev/null | jq -r ".[] | select(.Name == \"$project\") | .ConfigFiles" | head -n1)
                echo "  docker compose -p $project -f $config_file stop"
            fi
        done
        return 0
    fi
    
    # 각 프로젝트 중지
    local failed=0
    echo "$projects" | while read -r project; do
        if [ -n "$project" ]; then
            local config_file
            config_file=$(docker compose ls --format json 2>/dev/null | jq -r ".[] | select(.Name == \"$project\") | .ConfigFiles" | head -n1)
            
            if [ -z "$config_file" ] || [ "$config_file" = "null" ]; then
                echo -e "${RED}  ✗ $project: 설정 파일을 찾을 수 없습니다${NC}"
                failed=1
                continue
            fi
            
            echo -e "${YELLOW}중지 중: $project${NC}"
            if docker compose -p "$project" -f "$config_file" stop; then
                echo -e "${GREEN}  ✓ $project 중지 완료${NC}"
            else
                echo -e "${RED}  ✗ $project 중지 실패${NC}"
                failed=1
            fi
            echo ""
        fi
    done
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}=== 모든 프로젝트 중지 완료 ===${NC}"
        return 0
    else
        error_exit "일부 프로젝트 중지에 실패했습니다."
    fi
}

# 메인 로직
main() {
    local dry_run=false
    local verbose=false
    
    # 인자 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run=true
                shift
                ;;
            --verbose|-v)
                verbose=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--dry-run] [--verbose]"
                echo ""
                echo "옵션:"
                echo "  --dry-run    실제로 중지하지 않고 예상 동작만 표시"
                echo "  --verbose    상세한 출력"
                echo "  --help       이 도움말 표시"
                exit 0
                ;;
            *)
                echo -e "${RED}알 수 없는 옵션: $1${NC}" >&2
                echo "사용법: $0 [--dry-run] [--verbose] [--help]"
                exit 1
                ;;
        esac
    done
    
    if [ "$verbose" = "true" ]; then
        set -x
    fi
    
    stop_all_compose "$dry_run"
}

# 스크립트 실행
main "$@"

