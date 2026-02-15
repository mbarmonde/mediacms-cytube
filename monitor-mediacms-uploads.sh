#!/bin/bash
# dev-v0.2.0 - mediacms-monitor.sh - Performance diagnostics for MediaCMS video processing

#####
# CHANGELOG
# v0.2.0 - Enhanced readability
# v0.1.0 - Initial release
#####

# Stored at: /mediacms/monitor-mediacms-uploads.sh

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
WORKER_CONTAINER="mediacms_celery_worker_1"
DURATION=60
LOG_FILE="mediacms-perf-$(date +%Y%m%d-%H%M%S).log"

# Initialize tracking variables
CPU_SAMPLES=0
CPU_TOTAL=0
IO_HIGH_COUNT=0
MEMORY_WARNINGS=0

# Header
clear
echo -e "${BOLD}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║         MediaCMS Performance Diagnostics Monitor v1.0          ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Worker Container:${NC} $WORKER_CONTAINER"
echo -e "${CYAN}Duration:${NC} ${DURATION}s (monitoring in 5-second intervals)"
echo -e "${CYAN}Log File:${NC} $LOG_FILE"
echo ""
echo -e "${YELLOW}→ Upload a video to MediaCMS now to begin diagnostics...${NC}"
echo ""
sleep 3

# Start logging
{
    echo "MediaCMS Performance Log - $(date)"
    echo "Container: $WORKER_CONTAINER"
    echo "=========================================="
} > "$LOG_FILE"

# Monitoring loop
for i in $(seq 1 $((DURATION / 5))); do
    TIMESTAMP=$(date "+%H:%M:%S")
    
    echo -e "${BOLD}┌─ Sample $i/$((DURATION / 5)) at $TIMESTAMP ─────────────────────────────────────┐${NC}"
    
    # Container Stats
    echo -e "${CYAN}├─ Container Resources:${NC}"
    CONTAINER_STATS=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" "$WORKER_CONTAINER" 2>/dev/null | tail -n +2)
    
    if [ -z "$CONTAINER_STATS" ]; then
        echo -e "${RED}   ⚠ Container not found or not running${NC}"
    else
        echo "$CONTAINER_STATS" | while read -r line; do
            CPU_PERC=$(echo "$line" | awk '{print $2}' | tr -d '%')
            MEM_USAGE=$(echo "$line" | awk '{print $3}')
            
            # Color code based on CPU usage
            if (( $(echo "$CPU_PERC > 90" | bc -l 2>/dev/null || echo 0) )); then
                echo -e "${RED}   ⚠ CPU: ${CPU_PERC}% (CRITICAL) │ Memory: $MEM_USAGE${NC}"
                CPU_HIGH_COUNT=$((CPU_HIGH_COUNT + 1))
            elif (( $(echo "$CPU_PERC > 70" | bc -l 2>/dev/null || echo 0) )); then
                echo -e "${YELLOW}   ⚡ CPU: ${CPU_PERC}% (HIGH) │ Memory: $MEM_USAGE${NC}"
            else
                echo -e "${GREEN}   ✓ CPU: ${CPU_PERC}% (NORMAL) │ Memory: $MEM_USAGE${NC}"
            fi
            
            CPU_TOTAL=$(echo "$CPU_TOTAL + $CPU_PERC" | bc 2>/dev/null || echo "$CPU_TOTAL")
            CPU_SAMPLES=$((CPU_SAMPLES + 1))
        done
    fi
    
    # Disk I/O Stats
    echo -e "${CYAN}├─ Disk I/O Performance:${NC}"
    IOSTAT_OUTPUT=$(iostat -x 1 2 2>/dev/null | grep -A100 "Device" | tail -n +2 | head -5)
    
    if [ -z "$IOSTAT_OUTPUT" ]; then
        echo -e "${YELLOW}   ⚠ iostat not available (install: apt install sysstat)${NC}"
    else
        echo "$IOSTAT_OUTPUT" | while read -r line; do
            DEVICE=$(echo "$line" | awk '{print $1}')
            UTIL=$(echo "$line" | awk '{print $NF}' | cut -d. -f1)
            AWAIT=$(echo "$line" | awk '{print $(NF-4)}')
            
            if [ "$UTIL" -gt 85 ] 2>/dev/null; then
                echo -e "${RED}   ⚠ $DEVICE: ${UTIL}% utilized │ await: ${AWAIT}ms (BOTTLENECK)${NC}"
                IO_HIGH_COUNT=$((IO_HIGH_COUNT + 1))
            elif [ "$UTIL" -gt 60 ] 2>/dev/null; then
                echo -e "${YELLOW}   ⚡ $DEVICE: ${UTIL}% utilized │ await: ${AWAIT}ms${NC}"
            else
                echo -e "${GREEN}   ✓ $DEVICE: ${UTIL}% utilized │ await: ${AWAIT}ms${NC}"
            fi
        done
    fi
    
    # FFmpeg Process Check
    echo -e "${CYAN}├─ Active Encoding Processes:${NC}"
    FFMPEG_COUNT=$(docker exec "$WORKER_CONTAINER" ps aux 2>/dev/null | grep -c "[f]fmpeg" || echo "0")
    
    if [ "$FFMPEG_COUNT" -gt 0 ]; then
        echo -e "${GREEN}   ✓ $FFMPEG_COUNT FFmpeg process(es) running${NC}"
        
        # Try to extract encoding speed from logs (last 5 lines)
        SPEED_INFO=$(docker logs --tail 5 "$WORKER_CONTAINER" 2>&1 | grep -oP "speed=\s*\K[\d.]+x" | tail -1)
        if [ -n "$SPEED_INFO" ]; then
            SPEED_NUM=$(echo "$SPEED_INFO" | tr -d 'x')
            if (( $(echo "$SPEED_NUM < 0.5" | bc -l 2>/dev/null || echo 0) )); then
                echo -e "${RED}   ⚠ Encoding speed: ${SPEED_INFO} (VERY SLOW)${NC}"
            elif (( $(echo "$SPEED_NUM < 1.0" | bc -l 2>/dev/null || echo 0) )); then
                echo -e "${YELLOW}   ⚡ Encoding speed: ${SPEED_INFO} (slower than realtime)${NC}"
            else
                echo -e "${GREEN}   ✓ Encoding speed: ${SPEED_INFO}${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}   ⚡ No active encoding (waiting for jobs)${NC}"
    fi
    
    echo -e "${BOLD}└──────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    
    # Log to file
    {
        echo "[$TIMESTAMP] Container: $CONTAINER_STATS"
        echo "[$TIMESTAMP] Disk I/O: $(echo "$IOSTAT_OUTPUT" | head -1)"
        echo "[$TIMESTAMP] FFmpeg processes: $FFMPEG_COUNT"
        echo "---"
    } >> "$LOG_FILE"
    
    sleep 5
done

# Summary Report
echo ""
echo -e "${BOLD}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                     DIAGNOSTIC SUMMARY                         ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Calculate average CPU
AVG_CPU=0
if [ "$CPU_SAMPLES" -gt 0 ]; then
    AVG_CPU=$(echo "scale=1; $CPU_TOTAL / $CPU_SAMPLES" | bc 2>/dev/null || echo "0")
fi

printf "${CYAN}%-30s${NC} " "Average CPU Usage:"
if (( $(echo "$AVG_CPU > 90" | bc -l 2>/dev/null || echo 0) )); then
    printf "${RED}${BOLD}%.1f%% (CPU BOTTLENECK DETECTED)${NC}\n" "$AVG_CPU"
    echo -e "${RED}→ Recommendation: Upgrade to more/faster CPU cores${NC}"
elif (( $(echo "$AVG_CPU > 70" | bc -l 2>/dev/null || echo 0) )); then
    printf "${YELLOW}%.1f%% (High utilization)${NC}\n" "$AVG_CPU"
    echo -e "${YELLOW}→ Recommendation: Consider CPU upgrade or reduce encoding profiles${NC}"
else
    printf "${GREEN}%.1f%% (Healthy)${NC}\n" "$AVG_CPU"
fi

printf "${CYAN}%-30s${NC} " "High I/O Utilization Events:"
if [ "$IO_HIGH_COUNT" -gt 5 ]; then
    printf "${RED}${BOLD}%d (DISK I/O BOTTLENECK DETECTED)${NC}\n" "$IO_HIGH_COUNT"
    echo -e "${RED}→ Recommendation: Upgrade to NVMe/SSD storage${NC}"
elif [ "$IO_HIGH_COUNT" -gt 0 ]; then
    printf "${YELLOW}%d (Some disk stress)${NC}\n" "$IO_HIGH_COUNT"
else
    printf "${GREEN}%d (No issues)${NC}\n" "$IO_HIGH_COUNT"
fi

echo ""
echo -e "${CYAN}Full log saved to:${NC} ${BOLD}$LOG_FILE${NC}"
echo ""

# Next steps
echo -e "${BOLD}Next Steps:${NC}"
echo -e "  1. Review full logs: ${CYAN}cat $LOG_FILE${NC}"
echo -e "  2. Check detailed I/O: ${CYAN}sudo iotop -o -P${NC}"
echo -e "  3. Monitor live CPU: ${CYAN}htop${NC}"
echo -e "  4. View FFmpeg output: ${CYAN}docker logs -f $WORKER_CONTAINER${NC}"
echo ""
