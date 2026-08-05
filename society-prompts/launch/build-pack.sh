#!/usr/bin/env bash
# Regenerate the launch pack in ready/ from the briefs in ../ plus the values in LOCALE.md.
#
#   ./build-pack.sh
#
# Each output file is one complete paste unit: setup + working agreement + the brief with your
# locale substituted in + deliverables and reporting rules. Placeholders you left blank in
# LOCALE.md stay as [BRACKETED] and are reported per file.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$(dirname "$here")"
out="$here/ready"
locale_file="$here/LOCALE.md"
preamble="$here/preamble.txt"
postamble="$here/postamble.txt"

for f in "$preamble" "$postamble"; do
  [ -f "$f" ] || { echo "missing template: $f" >&2; exit 1; }
done

mkdir -p "$out"
rm -f "$out"/*.txt

# ---- read locale values -------------------------------------------------------------------
declare -A vals=()
if [ -f "$locale_file" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^([A-Z_]+)=(.*)$ ]] || continue
    k="${BASH_REMATCH[1]}"
    v="${BASH_REMATCH[2]}"
    v="${v#"${v%%[![:space:]]*}"}"
    v="${v%"${v##*[![:space:]]}"}"
    if [ -n "$v" ]; then
      case "$v" in
        *'|'*) echo "LOCALE.md: value for $k contains '|', which is not supported. Skipping." >&2 ;;
        *) vals["$k"]="$v" ;;
      esac
    fi
  done < "$locale_file"
fi

if [ "${#vals[@]}" -eq 0 ]; then
  echo "No values set in LOCALE.md — generating with all placeholders intact."
else
  echo "Substituting ${#vals[@]} value(s) from LOCALE.md: ${!vals[*]}"
fi
echo

# ---- generate -----------------------------------------------------------------------------
count=0
for f in "$src"/[0-9][0-9]-*.md; do
  base="$(basename "$f" .md)"
  num="${base%%-*}"
  [ "$num" = "00" ] && continue           # 00 is the master frame, not a project
  slug="${base#*-}"

  # Title: first heading, minus the "NN — " prefix.
  title="$(head -1 "$f" | sed -e 's/^#[[:space:]]*//' -e 's/^[0-9]\{2\}[[:space:]]*—[[:space:]]*//')"

  body="$(mktemp)"
  # Everything between the first ```text fence and the next closing fence.
  awk '/^```text$/ {inblock=1; next} /^```$/ {if (inblock) exit} inblock {print}' "$f" > "$body"

  if [ ! -s "$body" ]; then
    echo "  !! $base — could not extract a brief block, skipping" >&2
    rm -f "$body"
    continue
  fi

  for k in "${!vals[@]}"; do
    sed -i.bak "s|\[$k\]|${vals[$k]}|g" "$body" && rm -f "$body.bak"
  done

  remaining="$(grep -o '\[[A-Z_]\{3,\}\]' "$body" | sort -u | tr '\n' ' ' || true)"
  remaining="${remaining%"${remaining##*[![:space:]]}"}"

  if [ -n "$remaining" ]; then
    note="$(printf '\nBefore you begin, note that this brief still contains unfilled placeholders:\n\n    %s\n\nI have not given you those values. Do not stop to ask. Where one blocks a concrete decision,\nchoose the most reasonable interpretation, write it down under an ASSUMPTIONS heading in\nSTATUS.md, and keep building. Flag every place a missing value materially changed what you\nbuilt.' "$remaining")"
    note="${note}"$'\n'
  else
    note=""
  fi

  dest="$out/$base.txt"
  {
    awk -v t="$title" -v s="$slug" -v n="$note" '
      { gsub(/\{\{TITLE\}\}/, t); gsub(/\{\{SLUG\}\}/, s); gsub(/\{\{PLACEHOLDER_NOTE\}\}/, n); print }
    ' "$preamble"
    cat "$body"
    cat "$postamble"
  } > "$dest"

  rm -f "$body"
  count=$((count + 1))

  if [ -n "$remaining" ]; then
    printf '  %-42s unfilled: %s\n' "$base.txt" "$remaining"
  else
    printf '  %-42s ready\n' "$base.txt"
  fi
done

echo
echo "Wrote $count file(s) to $out"
echo "Each one is a complete paste unit. Open a new chat, paste one file, that's the whole setup."
