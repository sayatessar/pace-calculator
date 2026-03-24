#!/bin/bash

# ============================================================
#  🏃 PACE CALCULATOR / ESTIMATOR
#  Calculate your running pace based on distance & finish time
# ============================================================

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

print_banner() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}${BOLD}║        🏃 RUNNING PACE CALCULATOR        ║${RESET}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════╝${RESET}"
    echo ""
}

print_usage() {
    echo -e "${BOLD}Usage:${RESET}"
    echo -e "  $0 <distance> <finish_time>"
    echo ""
    echo -e "${BOLD}Distance options:${RESET}"
    echo -e "  ${YELLOW}5K${RESET}   - 5 Kilometers  (5.0 km)"
    echo -e "  ${YELLOW}10K${RESET}  - 10 Kilometers (10.0 km)"
    echo -e "  ${YELLOW}HM${RESET}   - Half Marathon (21.0975 km)"
    echo -e "  ${YELLOW}FM${RESET}   - Full Marathon (42.195 km)"
    echo ""
    echo -e "${BOLD}Finish time format:${RESET}  ${YELLOW}HH:MM:SS${RESET}"
    echo ""
    echo -e "${BOLD}Examples:${RESET}"
    echo -e "  $0 5K 0:25:00"
    echo -e "  $0 10K 0:55:00"
    echo -e "  $0 HM 1:45:00"
    echo -e "  $0 FM 3:30:00"
    echo ""
}

# ── Helper: convert HH:MM:SS → total seconds ──────────────────────────────────
time_to_seconds() {
    local t="$1"
    local h m s
    IFS=':' read -r h m s <<< "$t"
    # strip leading zeros to avoid octal interpretation
    h=$((10#$h)); m=$((10#$m)); s=$((10#$s))
    echo $(( h*3600 + m*60 + s ))
}

# ── Helper: format seconds → HH:MM:SS or MM:SS ────────────────────────────────
format_time() {
    local total_sec="$1"
    local h=$(( total_sec / 3600 ))
    local m=$(( (total_sec % 3600) / 60 ))
    local s=$(( total_sec % 60 ))
    if [[ $h -gt 0 ]]; then
        printf "%d:%02d:%02d" "$h" "$m" "$s"
    else
        printf "%d:%02d" "$m" "$s"
    fi
}

# ── Helper: format pace seconds → MM:SS /km ───────────────────────────────────
format_pace() {
    local pace_sec="$1"
    local m=$(( pace_sec / 60 ))
    local s=$(( pace_sec % 60 ))
    printf "%d:%02d" "$m" "$s"
}

# ── Validate time format HH:MM:SS ────────────────────────────────────────────
validate_time() {
    local t="$1"
    if [[ ! "$t" =~ ^[0-9]{1,2}:[0-5][0-9]:[0-5][0-9]$ ]]; then
        echo -e "${RED}❌  Invalid time format '${t}'. Please use HH:MM:SS (e.g. 1:45:00)${RESET}"
        exit 1
    fi
}

# ── Framework selector ────────────────────────────────────────────────────────
select_framework() {
    echo -e "${BOLD}Select effort zone framework:${RESET}"
    echo -e "  ${YELLOW}[1]${RESET} General / Fixed Thresholds"
    echo -e "       ${CYAN}Simple universal pace brackets (default)${RESET}"
    echo -e "  ${YELLOW}[2]${RESET} Jack Daniels' VDOT Zones"
    echo -e "       ${CYAN}Based on physiological training zones (Easy / Marathon / Threshold / Interval / Repetition)${RESET}"
    echo -e "  ${YELLOW}[3]${RESET} Heart Rate Zone Model (5-Zone, pace proxy)"
    echo -e "       ${CYAN}HR zone equivalents approximated via pace (assumes average recreational runner)${RESET}"
    echo -e "  ${YELLOW}[4]${RESET} RPE – Rate of Perceived Exertion (1–10)"
    echo -e "       ${CYAN}How hard it feels, mapped to pace${RESET}"
    echo ""
    while true; do
        read -rp "$(echo -e "${YELLOW}Choose framework [1–4] (default: 1): ${RESET}")" FW_CHOICE
        FW_CHOICE="${FW_CHOICE:-1}"
        if [[ "$FW_CHOICE" =~ ^[1-4]$ ]]; then
            FRAMEWORK="$FW_CHOICE"
            return
        fi
        echo -e "${RED}  ❌ Invalid choice. Please enter 1–4.${RESET}"
    done
}

# ── Get zone label based on framework ─────────────────────────────────────────
get_zone() {
    local pace=$1
    local fw=$2

    case "$fw" in
        1)  # General / Fixed Thresholds
            FW_NAME="General / Fixed Thresholds"
            if   [[ $pace -le 210 ]]; then ZONE="${RED}🔥 Elite / Race Pace${RESET}"
            elif [[ $pace -le 270 ]]; then ZONE="${YELLOW}💨 Fast / Threshold${RESET}"
            elif [[ $pace -le 330 ]]; then ZONE="${GREEN}🏃 Moderate / Tempo${RESET}"
            elif [[ $pace -le 420 ]]; then ZONE="${BLUE}🚶 Easy / Aerobic${RESET}"
            else                           ZONE="${CYAN}🐢 Recovery / Walk-Run${RESET}"
            fi ;;
        2)  # Jack Daniels' VDOT
            FW_NAME="Jack Daniels' VDOT Zones"
            if   [[ $pace -le 180 ]]; then ZONE="${RED}🔥 R – Repetition (Speed/Economy)${RESET}"
            elif [[ $pace -le 228 ]]; then ZONE="${YELLOW}💨 I – Interval (VO2max)${RESET}"
            elif [[ $pace -le 270 ]]; then ZONE="${YELLOW}🎯 T – Threshold (Lactate)${RESET}"
            elif [[ $pace -le 330 ]]; then ZONE="${GREEN}🏅 M – Marathon Pace${RESET}"
            elif [[ $pace -le 420 ]]; then ZONE="${BLUE}🚶 E – Easy / Long Run${RESET}"
            else                           ZONE="${CYAN}🐢 Recovery${RESET}"
            fi ;;
        3)  # Heart Rate Zone Model
            FW_NAME="Heart Rate Zone Model (5-Zone, pace proxy)"
            if   [[ $pace -le 210 ]]; then ZONE="${RED}🔥 Zone 5 – Max / Anaerobic (90–100% HRmax)${RESET}"
            elif [[ $pace -le 252 ]]; then ZONE="${YELLOW}💨 Zone 4 – Hard / Threshold (80–90% HRmax)${RESET}"
            elif [[ $pace -le 312 ]]; then ZONE="${GREEN}🏃 Zone 3 – Moderate / Aerobic (70–80% HRmax)${RESET}"
            elif [[ $pace -le 390 ]]; then ZONE="${BLUE}🚶 Zone 2 – Easy / Fat Burn (60–70% HRmax)${RESET}"
            else                           ZONE="${CYAN}🐢 Zone 1 – Recovery (<60% HRmax)${RESET}"
            fi ;;
        4)  # RPE
            FW_NAME="RPE – Rate of Perceived Exertion (1–10)"
            if   [[ $pace -le 210 ]]; then ZONE="${RED}🔥 RPE 9–10 – Maximum / All-out effort${RESET}"
            elif [[ $pace -le 255 ]]; then ZONE="${YELLOW}💨 RPE 7–8 – Very hard, limited speech${RESET}"
            elif [[ $pace -le 315 ]]; then ZONE="${GREEN}🏃 RPE 5–6 – Challenging but sustainable${RESET}"
            elif [[ $pace -le 405 ]]; then ZONE="${BLUE}🚶 RPE 3–4 – Comfortable, conversational${RESET}"
            else                           ZONE="${CYAN}🐢 RPE 1–2 – Very light, warm-up/recovery${RESET}"
            fi ;;
    esac
}

# ── Main ──────────────────────────────────────────────────────────────────────
print_banner

# Parse arguments (or prompt interactively)
if [[ $# -eq 2 ]]; then
    DISTANCE_INPUT="$1"
    FINISH_TIME="$2"
    FRAMEWORK="1"   # default when using CLI args
elif [[ $# -eq 0 ]]; then
    echo -e "${BOLD}Supported distances:${RESET} 5K / 10K / HM / FM"
    read -rp "$(echo -e "${YELLOW}Enter distance: ${RESET}")" DISTANCE_INPUT
    read -rp "$(echo -e "${YELLOW}Enter finish time (HH:MM:SS): ${RESET}")" FINISH_TIME
    echo ""
    select_framework
    echo ""
else
    print_usage
    exit 1
fi

# ── Resolve distance in km ────────────────────────────────────────────────────
DISTANCE_UPPER=$(echo "$DISTANCE_INPUT" | tr '[:lower:]' '[:upper:]')

case "$DISTANCE_UPPER" in
    5K)
        DIST_KM="5.0"
        DIST_LABEL="5K"
        ;;
    10K)
        DIST_KM="10.0"
        DIST_LABEL="10K"
        ;;
    HM|HALFMARATHON|HALF)
        DIST_KM="21.0975"
        DIST_LABEL="Half Marathon (HM)"
        ;;
    FM|FULLMARATHON|FULL|MARATHON)
        DIST_KM="42.195"
        DIST_LABEL="Full Marathon (FM)"
        ;;
    *)
        echo -e "${RED}❌  Unknown distance '${DISTANCE_INPUT}'.${RESET}"
        echo -e "    Supported: ${YELLOW}5K, 10K, HM, FM${RESET}"
        exit 1
        ;;
esac

# ── Validate finish time ──────────────────────────────────────────────────────
validate_time "$FINISH_TIME"

TOTAL_SEC=$(time_to_seconds "$FINISH_TIME")

if [[ $TOTAL_SEC -le 0 ]]; then
    echo -e "${RED}❌  Finish time must be greater than 00:00:00${RESET}"
    exit 1
fi

# ── Calculate pace (seconds per km) using awk for float division ──────────────
PACE_SEC_KM=$(awk "BEGIN { printf \"%d\", $TOTAL_SEC / $DIST_KM }")
PACE_SEC_MILE=$(awk "BEGIN { printf \"%d\", $TOTAL_SEC / ($DIST_KM / 1.60934) }")

# ── Calculate speed (km/h) ────────────────────────────────────────────────────
SPEED_KMH=$(awk "BEGIN { printf \"%.2f\", ($DIST_KM / $TOTAL_SEC) * 3600 }")
SPEED_MPH=$(awk "BEGIN { printf \"%.2f\", ($DIST_KM / 1.60934 / $TOTAL_SEC) * 3600 }")

# ── Estimated split times ─────────────────────────────────────────────────────
SPLIT_1K_SEC=$PACE_SEC_KM
SPLIT_5K_SEC=$(awk "BEGIN { printf \"%d\", $PACE_SEC_KM * 5 }")
SPLIT_10K_SEC=$(awk "BEGIN { printf \"%d\", $PACE_SEC_KM * 10 }")
SPLIT_HM_SEC=$(awk "BEGIN { printf \"%d\", $PACE_SEC_KM * 21.0975 }")

# ── Output results ────────────────────────────────────────────────────────────
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  ${BOLD}Distance  :${RESET} ${GREEN}${DIST_LABEL}${RESET} (${DIST_KM} km)"
echo -e "  ${BOLD}Target    :${RESET} ${GREEN}${FINISH_TIME}${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "${CYAN}${BOLD}  📊 PACE${RESET}"
echo -e "  ├─ Per km   : ${YELLOW}${BOLD}$(format_pace $PACE_SEC_KM) /km${RESET}"
echo -e "  └─ Per mile : ${YELLOW}${BOLD}$(format_pace $PACE_SEC_MILE) /mi${RESET}"
echo ""
echo -e "${CYAN}${BOLD}  ⚡ SPEED${RESET}"
echo -e "  ├─ km/h     : ${YELLOW}${BOLD}${SPEED_KMH} km/h${RESET}"
echo -e "  └─ mph      : ${YELLOW}${BOLD}${SPEED_MPH} mph${RESET}"
echo ""
echo -e "${CYAN}${BOLD}  🏁 ESTIMATED SPLIT TIMES (at this pace)${RESET}"
echo -e "  ├─ 1 km     : $(format_time $SPLIT_1K_SEC)"
echo -e "  ├─ 5K       : $(format_time $SPLIT_5K_SEC)"
echo -e "  ├─ 10K      : $(format_time $SPLIT_10K_SEC)"
echo -e "  └─ Half (HM): $(format_time $SPLIT_HM_SEC)"
echo ""

# ── Effort zone estimate ──────────────────────────────────────────────────────
get_zone "$PACE_SEC_KM" "$FRAMEWORK"

echo -e "${CYAN}${BOLD}  🎯 EFFORT ZONE  ${RESET}${BOLD}(${FW_NAME})${RESET}"
echo -e "  └─ ${ZONE}"
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  ${GREEN}${BOLD}Good luck with your run! 💪${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
