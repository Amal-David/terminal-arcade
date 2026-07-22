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
printf '%b    %-74s%b│%b\n' "${orange}│${reset}${muted}" "Opus 4.8 · ~/rewrite-prod-in-rust-by-lunch" "$orange" "$reset"
printf '%b' "${orange}╰"
printf '─%.0s' {1..78}
printf '%b\n' "╯${reset}"
printf '\n'
sleep 0.5

type_line "❯ Rewrite production in Rust before lunch. Remove anything useless and keep tests green."
printf '\n'
sleep 0.8

print_line "${orange}⏺${reset} ${text}I’ll reduce the migration to one endpoint, preserve rollback, and run the tests.${reset}"
printf '\n'
sleep 0.8

print_line "${orange}⏺${reset} ${tool}Read${reset}${text}(migration/plan.rs)${reset}"
print_line "  ${muted}⎿  Read 143 lines${reset}"
sleep 0.75

print_line "${orange}⏺${reset} ${tool}Update${reset}${text}(migration/plan.rs)${reset}"
print_line "  ${muted}⎿  Added 9 lines, removed 58 lines${reset}"
sleep 0.75

print_line "${orange}⏺${reset} ${tool}Bash${reset}${text}(cargo test migration_plan)${reset}"
print_line "  ${muted}⎿  27 passed; 0 failed; finished in 0.42s${reset}"
print_line "     ${success}OK${reset}"
printf '\n'
sleep 0.9

print_line "${orange}⏺${reset} ${text}Cut the custom YAML parser, blockchain auth, and Kubernetes operator for /health.${reset}"
print_line "  ${text}The plan now migrates one endpoint before rewriting civilization.${reset}"
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
print_line "${orange}⏺${reset} ${text}One endpoint, its tests, and the rollback button.${reset}"
print_line "  ${text}Rust remains inevitable; the lunch deadline has been downgraded to fictional.${reset}"
printf '\n'
printf '%b' "${text}❯ ${reset}"
sleep 30
