#!/bin/bash

input=$(cat)

# ─────────────────────────────────────────────────────────────
# Extract JSON fields
# ─────────────────────────────────────────────────────────────
VERSION=$(echo "$input" | jq -r '.version // "?"')
MODEL=$(echo "$input" | jq -r '.model.display_name // "Claude"')

# Session totals
TOTAL_IN=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
TOTAL_OUT=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')

# Current context window usage
CTX_IN=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
CTX_OUT=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // 0')
CTX_CACHE_W=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
CTX_CACHE_R=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
CTX_MAX=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')

# Current context = all tokens in current turn
CTX_USED=$((CTX_IN + CTX_OUT + CTX_CACHE_W + CTX_CACHE_R))

# Cost and duration
COST_USD=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
API_DURATION_MS=$(echo "$input" | jq -r '.cost.total_api_duration_ms // 0')

# Lines changed
LINES_ADD=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
LINES_DEL=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')

# Git info
REPO="—"
BRANCH="—"
if git rev-parse --git-dir > /dev/null 2>&1; then
    REPO=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "—")
    BRANCH=$(git branch --show-current 2>/dev/null || echo "—")
fi

# ─────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_DIM="\033[2m"
C_CYAN="\033[38;5;80m"
C_GREEN="\033[38;5;114m"
C_YELLOW="\033[38;5;222m"
C_ORANGE="\033[38;5;209m"
C_RED="\033[38;5;203m"
C_PURPLE="\033[38;5;141m"
C_BLUE="\033[38;5;75m"
C_GRAY="\033[38;5;245m"
C_WHITE="\033[38;5;255m"

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
fmt() {
    local n=$1
    if [ "$n" -ge 1000000 ]; then
        printf "%.1fM" "$(echo "scale=2; $n / 1000000" | bc)"
    elif [ "$n" -ge 1000 ]; then
        printf "%.1fK" "$(echo "scale=2; $n / 1000" | bc)"
    else
        printf "%d" "$n"
    fi
}

fmt_duration() {
    local ms=$1
    local sec=$((ms / 1000))
    local min=$((sec / 60))
    local hr=$((min / 60))

    if [ "$hr" -gt 0 ]; then
        printf "%dh%dm" "$hr" "$((min % 60))"
    elif [ "$min" -gt 0 ]; then
        printf "%dm%ds" "$min" "$((sec % 60))"
    else
        printf "%ds" "$sec"
    fi
}

fmt_cost() {
    local cost=$1
    # Handle floating point
    if [ "$(echo "$cost >= 1" | bc -l)" -eq 1 ]; then
        printf "\$%.2f" "$cost"
    elif [ "$(echo "$cost >= 0.01" | bc -l)" -eq 1 ]; then
        printf "\$%.2f" "$cost"
    elif [ "$(echo "$cost > 0" | bc -l)" -eq 1 ]; then
        printf "\$%.3f" "$cost"
    else
        printf "\$0.00"
    fi
}

bar() {
    local used=$1 max=$2 width=$3
    local pct=0 filled=0
    
    [ "$max" -gt 0 ] && pct=$((used * 100 / max)) && filled=$((used * width / max))
    [ "$filled" -gt "$width" ] && filled=$width
    local empty=$((width - filled))
    
    # Color based on usage
    local c="$C_BLUE"
    [ "$pct" -ge 60 ] && c="$C_YELLOW"
    [ "$pct" -ge 80 ] && c="$C_ORANGE"
    [ "$pct" -ge 95 ] && c="$C_RED"
    
    local b=""
    for ((i=0; i<filled; i++)); do b+="━"; done
    for ((i=0; i<empty; i++)); do b+="─"; done
    
    echo -e "${c}${b}${C_RESET}"
}

# ─────────────────────────────────────────────────────────────
# Format values
# ─────────────────────────────────────────────────────────────
SESSION_TOTAL=$((TOTAL_IN + TOTAL_OUT))
CTX_PCT=$((CTX_USED * 100 / CTX_MAX))

# Cache efficiency (if cache is being used)
CACHE_TOTAL=$((CTX_CACHE_W + CTX_CACHE_R))
if [ "$CACHE_TOTAL" -gt 0 ]; then
    CACHE_HIT_PCT=$((CTX_CACHE_R * 100 / CACHE_TOTAL))
else
    CACHE_HIT_PCT=0
fi

# Lines formatting
if [ "$LINES_ADD" -gt 0 ] || [ "$LINES_DEL" -gt 0 ]; then
    LINES_FMT="${C_GREEN}+${LINES_ADD}${C_RESET} ${C_RED}-${LINES_DEL}${C_RESET}"
else
    LINES_FMT="${C_DIM}±0${C_RESET}"
fi

# Duration formatting
DURATION_FMT=$(fmt_duration "$DURATION_MS")

# Cost formatting
COST_FMT=$(fmt_cost "$COST_USD")

# ─────────────────────────────────────────────────────────────
# Build status line
# ─────────────────────────────────────────────────────────────
SEP="${C_GRAY}│${C_RESET}"

# Line 1: Project info + cost + duration
L1="${C_CYAN}${REPO}${C_RESET} ${SEP} ${C_GREEN}${BRANCH}${C_RESET} ${SEP} ${C_PURPLE}${MODEL}${C_RESET} ${C_DIM}v${VERSION}${C_RESET} ${SEP} ${C_GREEN}${COST_FMT}${C_RESET} ${SEP} ${C_YELLOW}${DURATION_FMT}${C_RESET}"

# Line 2: Context bar + token details
CTX_BAR=$(bar "$CTX_USED" "$CTX_MAX" 20)
L2="${C_BLUE}◆${C_RESET} ${CTX_BAR} ${C_WHITE}$(fmt $CTX_USED)${C_RESET}${C_DIM}/${C_RESET}${C_GRAY}$(fmt $CTX_MAX)${C_RESET} ${C_DIM}(${CTX_PCT}%)${C_RESET}"

# Line 3: Token breakdown + lines changed
# in/out tokens, cache stats, lines changed
L3="${C_CYAN}in:${C_RESET}$(fmt $TOTAL_IN) ${C_ORANGE}out:${C_RESET}$(fmt $TOTAL_OUT) ${SEP} ${C_PURPLE}cache:${C_RESET}$(fmt $CTX_CACHE_R)${C_DIM}r/${C_RESET}$(fmt $CTX_CACHE_W)${C_DIM}w${C_RESET} ${C_DIM}(${CACHE_HIT_PCT}%hit)${C_RESET} ${SEP} ${LINES_FMT}"

echo -e "$L1"
echo -e "$L2"
echo -e "$L3"