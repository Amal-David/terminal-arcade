#!/bin/zsh
set -eu

reset='\033[0m'
orange='\033[38;5;173m'
muted='\033[38;5;245m'
text='\033[38;5;252m'
tool='\033[38;5;117m'
success='\033[38;5;114m'
quote='\033[38;5;221m'

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
printf '%b' "${orange}╭─── Claude Code v2.1.217 "
printf '─%.0s' {1..53}
printf '%b\n' "╮${reset}"
printf '%b  %b✻%b %-74s%b│%b\n' "${orange}│${reset}" "$orange" "${reset}${text}" "Welcome back, Amal!" "$orange" "$reset"
printf '%b    %-74s%b│%b\n' "${orange}│${reset}${muted}" "Opus 4.8 · ~/moonshot-with-unit-tests" "$orange" "$reset"
printf '%b' "${orange}╰"
printf '─%.0s' {1..78}
printf '%b\n' "╯${reset}"
printf '\n'
sleep 0.5

type_line "❯ Make the Moon profitable by Friday. Delete anything useless and test the plan."
printf '\n'
sleep 0.8

print_line "${orange}⏺${reset} ${text}I’ll cut ceremonial scope, protect survival systems, and verify the launch plan.${reset}"
printf '\n'
sleep 0.8

print_line "${orange}⏺${reset} ${tool}Read${reset}${text}(moonshot/launch_plan.py)${reset}"
print_line "  ${muted}⎿  Read 86 lines${reset}"
sleep 0.75

print_line "${orange}⏺${reset} ${tool}Update${reset}${text}(moonshot/launch_plan.py)${reset}"
print_line "  ${muted}⎿  Added 6 lines, removed 41 lines${reset}"
sleep 0.75

print_line "${orange}⏺${reset} ${tool}Bash${reset}${text}(python3 -m unittest tests.test_launch_plan)${reset}"
print_line "  ${muted}⎿  Ran 27 tests in 0.42s${reset}"
print_line "     ${success}OK${reset}"
printf '\n'
sleep 0.9

print_line "${orange}⏺${reset} ${text}Cut the NFT gift shop, lunar loyalty points, and executive zero-gravity offsite.${reset}"
print_line "  ${text}The plan now funds oxygen before branding.${reset}"
printf '\n'
sleep 0.9

print_line "${muted}────────────────────────────── Bookshelf ──────────────────────────────${reset}"
print_line "${quote}📖 “Do nothing which is of no use.”${reset}"
print_line "   ${text}— Miyamoto Musashi, ${orange}The Book of Five Rings${reset}"
print_line "${muted}────────────────────────────────────────────────────────────────────────${reset}"
printf '\n'
sleep 0.8

type_line "❯ Good. What survived?"
printf '\n'
sleep 0.6
print_line "${orange}⏺${reset} ${text}Oxygen, return fuel, and one honest spreadsheet.${reset}"
print_line "  ${text}The Moon remains ambitious; the roadmap is now merely financially irresponsible.${reset}"
printf '\n'
printf '%b' "${text}❯ ${reset}"
sleep 30
