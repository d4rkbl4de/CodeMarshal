#!/bin/bash
# Monitor wrapper for CodeMarshal observation with memory and file tracking

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get start time
START=$(date +%s)

# Create log directory
LOG_DIR="$HOME/.codemarshal/logs"
mkdir -p "$LOG_DIR"

# Log file for this run
LOG_FILE="$LOG_DIR/monitor_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}🚀 Starting CodeMarshal with monitoring...${NC}"
echo "Command: codemarshal observe $*"
echo "Log file: $LOG_FILE"
echo

# Start CodeMarshal in background
codemarshal observe "$@" &
PID=$!

# Function to get memory usage
get_memory() {
    if command -v ps >/dev/null 2>&1; then
        MEM=$(ps -o rss= -p $PID 2>/dev/null | awk '{print int($1/1024)}')
        echo "${MEM:-0}"
    else
        echo "0"
    fi
}

# Function to count processed files
get_file_count() {
    local count=0
    if [ -d "$HOME/.codemarshal/sessions" ]; then
        # Find the latest session
        latest_session=$(find "$HOME/.codemarshal/sessions" -maxdepth 1 -type d -name "session_*" | sort | tail -1)
        if [ -n "$latest_session" ] && [ -d "$latest_session/observations" ]; then
            count=$(find "$latest_session/observations" -name "*.observation.json" 2>/dev/null | wc -l)
        fi
    fi
    echo $count
}

# Function to check for corruption markers
check_corruption() {
    local corruption_count=0
    if [ -d "$HOME/.codemarshal/storage/observations" ]; then
        corruption_count=$(find "$HOME/.codemarshal/storage/observations" -name "*.corrupted" 2>/dev/null | wc -l)
    fi
    echo $corruption_count
}

# Function to get disk usage
get_disk_usage() {
    if [ -d "$HOME/.codemarshal" ]; then
        du -sh "$HOME/.codemarshal" 2>/dev/null | cut -f1
    else
        echo "0B"
    fi
}

# Monitoring loop
echo -e "${YELLOW}Monitoring started (PID: $PID)${NC}"
echo "Press Ctrl+C to stop monitoring (CodeMarshal will continue)"
echo

# Track peak memory
PEAK_MEM=0
WARNINGS=0

while kill -0 $PID 2>/dev/null; do
    ELAPSED=$(( $(date +%s) - $START ))
    MEM=$(get_memory)
    FILES=$(get_file_count)
    CORRUPTION=$(check_corruption)
    DISK=$(get_disk_usage)
    
    # Track peak memory
    if [ "$MEM" -gt "$PEAK_MEM" ]; then
        PEAK_MEM=$MEM
    fi
    
    # Memory warnings
    if [ "$MEM" -gt 4096 ]; then
        echo -e "\r${RED}🚨 CRITICAL: ${MEM}MB memory usage!${NC} Time: ${ELAPSED}s | Files: ${FILES} | Disk: ${DISK} | Corruption: ${CORRUPTION}"
        WARNINGS=$((WARNINGS + 1))
    elif [ "$MEM" -gt 2048 ]; then
        echo -e "\r${YELLOW}⚠️ WARNING: ${MEM}MB memory usage${NC} Time: ${ELAPSED}s | Files: ${FILES} | Disk: ${DISK} | Corruption: ${CORRUPTION}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -ne "\r${GREEN}✓${NC} Time: ${ELAPSED}s | Memory: ${MEM}MB | Files: ${FILES} | Disk: ${DISK} | Corruption: ${CORRUPTION}"
    fi
    
    # Log to file
    echo "$(date '+%Y-%m-%d %H:%M:%S'),${ELAPSED},${MEM},${FILES},${CORRUPTION},${DISK}" >> "$LOG_FILE"
    
    sleep 2
done

# Get exit code
wait $PID
EXIT_CODE=$?

echo -e "\n\n${BLUE}📊 Monitoring Summary${NC}"
echo "=================="
echo "Exit Code: $EXIT_CODE"
echo "Total Time: $(( $(date +%s) - $START ))s"
echo "Peak Memory: ${PEAK_MEM}MB"
echo "Warnings Issued: $WARNINGS"
echo "Files Processed: $(get_file_count)"
echo "Corruption Markers: $(check_corruption)"
echo "Disk Usage: $(get_disk_usage)"
echo "Log File: $LOG_FILE"

# Check for boundary violations if constitutional analysis was used
if [[ "$*" == *"--constitutional"* ]]; then
    echo
    echo -e "${BLUE}🔍 Boundary Violation Check${NC}"
    echo "========================="
    
    # Look for boundary crossings in observations
    if [ -d "$HOME/.codemarshal/storage/observations" ]; then
        VIOLATIONS=$(grep -l "boundary_cross_lobe_import" "$HOME/.codemarshal/storage/observations"/*.json 2>/dev/null | wc -l)
        if [ "$VIOLATIONS" -gt 0 ]; then
            echo -e "${RED}❌ Found $VIOLATIONS files with boundary violations${NC}"
            echo "Check observation files for details:"
            find "$HOME/.codemarshal/storage/observations" -name "*.json" -exec grep -l "boundary_cross_lobe_import" {} \; 2>/dev/null | head -5
        else
            echo -e "${GREEN}✅ No boundary violations detected${NC}"
        fi
    fi
fi

# Storage integrity check
echo
echo -e "${BLUE}🔒 Storage Integrity Check${NC}"
echo "=========================="
if command -v python3 >/dev/null 2>&1; then
    python3 -c "
import sys
sys.path.insert(0, '$PWD')
from core.storage_integration import InvestigationStorage
storage = InvestigationStorage()
report = storage.verify_storage_integrity()
if report['is_corrupt']:
    print(f'❌ Corruption detected: {report[\"corruption_count\"]} issues')
    for issue in report['corruption_evidence'][:3]:
        print(f'   - {issue[\"path\"]}: {issue[\"type\"]}')
else:
    print('✅ Storage integrity verified')
" 2>/dev/null || echo "Could not verify storage integrity"
else
    echo "Python3 not available for integrity check"
fi

echo
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ CodeMarshal completed successfully${NC}"
else
    echo -e "${RED}❌ CodeMarshal failed with exit code $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
