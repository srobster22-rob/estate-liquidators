#!/bin/bash
# THE COLLECTOR'S SIDE: Chrome's --trace-gc over N settled steps of the pinned run on each
# build given (directories holding an index.html), through tiers.js with DEBUG=pw:browser
# so the browser's stdout reaches the trace file; the scavenges between "settled" and
# "stepped" counted, their pauses summed.
HERE=$(cd "$(dirname "$0")" && pwd); N=${N:-6000}
for B in "$@"; do
  T=$(mktemp -d); echo "--- $B"
  REPO=$B N=$N JSF="--allow-natives-syntax --trace-gc" DEBUG=pw:browser node $HERE/tiers.js > $T/log 2> $T/trace
  T1=$(grep -o "^[0-9T:.-]*Z settled" $T/log | cut -d' ' -f1); T2=$(grep -o "^[0-9T:.-]*Z stepped" $T/log | cut -d' ' -f1)
  awk -v a="$T1" -v b="$T2" '$1 > a && $1 < b' $T/trace > $T/window
  echo "$(grep -c 'Scavenge' $T/window) scavenges, $(grep -c 'Mark-Compact' $T/window) mark-compacts over $N steps; scavenge pauses $(grep 'Scavenge' $T/window | grep -oE '[0-9.]+ / [0-9.]+ ms' | awk '{s+=$1; if($1>m)m=$1} END {printf "%.1f ms total, max %.2f ms", s, m}')"
  rm -rf $T
done
