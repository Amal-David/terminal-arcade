#!/bin/zsh
set -eu

reset='\033[0m'
orange='\033[38;5;173m'
muted='\033[38;5;245m'
text='\033[38;5;252m'
tool='\033[38;5;117m'
success='\033[38;5;114m'
phrase='\033[38;5;221m'
blue='\033[38;5;111m'

print_line() {
  printf '%b\n' "$1"
}

type_line() {
  local value="$1"
  local index
  printf '%b' "$text"
  for (( index = 1; index <= ${#value}; index++ )); do
    printf '%s' "${value[index]}"
    sleep 0.018
  done
  printf '%b\n' "$reset"
}

clear
printf '%b' "${orange}╭─── Claude Code v2.1.14 "
printf '─%.0s' {1..54}
printf '%b\n' "╮${reset}"
printf '%b  %b✻%b %-74s%b│%b\n' "${orange}│${reset}" "$orange" "${reset}${text}" "Welcome back, Amal!" "$orange" "$reset"
printf '%b    %-74s%b│%b\n' "${orange}│${reset}${muted}" "Sonnet 4.5 · ~/polyglot" "$orange" "$reset"
printf '%b' "${orange}╰"
printf '─%.0s' {1..78}
printf '%b\n' "╯${reset}"
printf '\n'
sleep 0.5

type_line "❯ Add a due-card test for the German review scheduler."
printf '\n'
sleep 0.8

print_line "${orange}⏺${reset} ${text}I’ll trace the interval logic, add the regression case, and run it.${reset}"
printf '\n'
sleep 0.8

print_line "${orange}⏺${reset} ${tool}Read${reset}${text}(polyglot/scheduler.py)${reset}"
print_line "  ${muted}⎿  Read 96 lines${reset}"
sleep 0.75

print_line "${orange}⏺${reset} ${tool}Update${reset}${text}(tests/test_learning.py)${reset}"
print_line "  ${muted}⎿  Added 11 lines${reset}"
sleep 0.75

print_line "${orange}⏺${reset} ${tool}Bash${reset}${text}(python3 -m unittest tests.test_learning)${reset}"
print_line "  ${muted}⎿  Ran 24 tests in 0.28s${reset}"
print_line "     ${success}OK${reset}"
printf '\n'
sleep 0.9

print_line "${orange}⏺${reset} ${text}Added coverage for the one-day interval without changing review state.${reset}"
printf '\n'
sleep 0.9

print_line "${muted}────────────────────── Polyglot · English → German ───────────────────${reset}"
print_line "${blue}🌍 ${phrase}hello → hallo${reset}"
print_line "   ${text}Say it: ${phrase}HAH-loh${reset}  ${muted}· greeting${reset}"
print_line "${muted}────────────────────────────────────────────────────────────────────────${reset}"
printf '\n'
printf '%b' "${text}❯ ${reset}"
sleep 4
