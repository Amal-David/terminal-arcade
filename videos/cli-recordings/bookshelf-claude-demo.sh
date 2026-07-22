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
printf '%b' "${orange}╭─── Claude Code v2.1.14 "
printf '─%.0s' {1..54}
printf '%b\n' "╮${reset}"
printf '%b  %b✻%b %-74s%b│%b\n' "${orange}│${reset}" "$orange" "${reset}${text}" "Welcome back, Amal!" "$orange" "$reset"
printf '%b    %-74s%b│%b\n' "${orange}│${reset}${muted}" "Sonnet 4.5 · ~/terminal-arcade" "$orange" "$reset"
printf '%b' "${orange}╰"
printf '─%.0s' {1..78}
printf '%b\n' "╯${reset}"
printf '\n'
sleep 0.5

type_line "❯ Simplify the quote selector and run the focused tests."
printf '\n'
sleep 0.8

print_line "${orange}⏺${reset} ${text}I’ll trace the selection path, remove the duplicate branch, and verify it.${reset}"
printf '\n'
sleep 0.8

print_line "${orange}⏺${reset} ${tool}Read${reset}${text}(bookshelf/skill/quote_picker.py)${reset}"
print_line "  ${muted}⎿  Read 114 lines${reset}"
sleep 0.75

print_line "${orange}⏺${reset} ${tool}Update${reset}${text}(bookshelf/skill/quote_picker.py)${reset}"
print_line "  ${muted}⎿  Added 8 lines, removed 13 lines${reset}"
sleep 0.75

print_line "${orange}⏺${reset} ${tool}Bash${reset}${text}(python3 -m unittest tests.test_bookshelf_hook)${reset}"
print_line "  ${muted}⎿  Ran 19 tests in 0.31s${reset}"
print_line "     ${success}OK${reset}"
printf '\n'
sleep 0.9

print_line "${orange}⏺${reset} ${text}Simplified the candidate selection path and preserved unseen-first behavior.${reset}"
printf '\n'
sleep 0.9

print_line "${muted}────────────────────────────── Bookshelf ──────────────────────────────${reset}"
print_line "${quote}📖 “Do nothing which is of no use.”${reset}"
print_line "   ${text}— Miyamoto Musashi, ${orange}The Book of Five Rings${reset}"
print_line "${muted}────────────────────────────────────────────────────────────────────────${reset}"
printf '\n'
printf '%b' "${text}❯ ${reset}"
sleep 4
