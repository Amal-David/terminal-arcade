#!/bin/zsh
set -eu

# Render the redacted asciinema capture from a real Claude Code session.
# Claude Code 2.1.218 used Opus 4.8 in the disposable Friday-deploy Rust
# project. No tool call, edit, test result, response, or Polyglot Stop-hook
# output is synthesized by this renderer.

repo_root="${0:A:h:h:h}"
cast="$repo_root/videos/cli-recordings/polyglot-claude-actual.cast"
output_dir="$repo_root/sites/polyglot/assets"
source_gif="${TMPDIR:-/tmp}/polyglot-claude-actual-source.gif"
source_mp4="${TMPDIR:-/tmp}/polyglot-claude-actual-source.mp4"
source_poster="${TMPDIR:-/tmp}/polyglot-claude-actual-source.png"
readme_gif="${TMPDIR:-/tmp}/polyglot-claude-hero.gif"

agg \
  --quiet \
  --theme github-dark \
  --font-size 18 \
  --speed 1.25 \
  --idle-time-limit 0.7 \
  --fps-cap 20 \
  --last-frame-duration 4 \
  --select '0.3s..' \
  "$cast" \
  "$source_gif"

ffmpeg -y -loglevel error -i "$source_gif" \
  -an \
  -vf 'fps=30,pad=ceil(iw/2)*2:ceil(ih/2)*2' \
  -c:v libx264 \
  -preset medium \
  -crf 24 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$source_mp4"

ffmpeg -y -loglevel error -ss 23.5 -i "$source_mp4" \
  -frames:v 1 \
  "$source_poster"

# Compress the real setup and tool work, then hold the real Stop-hook phrase
# for four seconds with a modest camera push and a bounded highlight.
filter_complex='[0:v]split=3[a][b][c];
[a]trim=start=3.5:end=8.5,setpts=(PTS-STARTPTS)/3,fps=30,scale=1102:782,pad=1224:924:61:71:color=black[a1];
[b]trim=start=8.5:end=19,setpts=(PTS-STARTPTS)/3.5,fps=30,scale=1102:782,pad=1224:924:61:71:color=black[b1];
[c]trim=start=19:end=23.7,setpts=(PTS-STARTPTS)/2,fps=30,scale=1102:782,pad=1224:924:61:71:color=black[c1];
[a1][b1][c1]concat=n=3:v=1:a=0[work];
[1:v]scale=1102:782,pad=1224:924:61:71:color=black,zoompan=z=min(zoom+0.0012\,1.08):x=iw/2-(iw/zoom/2):y=ih-ih/zoom:d=120:s=1224x924:fps=30,drawbox=x=70:y=580:w=660:h=42:color=0x70d6ff@0.15:t=fill,drawbox=x=70:y=580:w=660:h=42:color=0x70d6ff@0.95:t=4[hero];
[work][hero]concat=n=2:v=1:a=0,format=yuv420p[out]'

ffmpeg -y -loglevel error \
  -i "$source_mp4" \
  -loop 1 -framerate 30 -i "$source_poster" \
  -filter_complex "$filter_complex" \
  -map '[out]' \
  -t 11 \
  -c:v libx264 \
  -preset medium \
  -crf 24 \
  -movflags +faststart \
  "$output_dir/polyglot-demo.mp4"

ffmpeg -y -loglevel error -ss 10 -i "$output_dir/polyglot-demo.mp4" \
  -frames:v 1 \
  "$output_dir/polyglot-poster.png"

ffmpeg -y -loglevel error -i "$output_dir/polyglot-demo.mp4" \
  -filter_complex 'fps=7,scale=720:-2:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=48:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5' \
  "$readme_gif"

print -r -- "$readme_gif"
