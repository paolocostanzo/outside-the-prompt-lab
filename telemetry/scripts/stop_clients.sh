#!/bin/bash
# Runs INSIDE the VM before the client logs are copied (D24 point 1): stops every client, its detached daemons and the lab
# servers, waits for them to exit, and exits non-zero if any is still running, so that databases and logs are not copied while
# a writer is alive. The patterns are written as [x]yz so that they never match this script's own command line.
# SAFETY: this script kills processes of the current user. It must never run on the host (on 17 Oct 2026 a test ran it on the
# host and closed the user's applications). It runs only when all three hold: Q4_IN_VM=1 is set explicitly by the caller, the
# VM's marker file ~/.agentlab_env exists, and the machine is not the lab host.
if [ "${Q4_IN_VM:-}" != "1" ] || [ ! -f "$HOME/.agentlab_env" ] || [ "$(hostname)" = "parrot" ]; then
  echo "refusing to run: not inside the lab VM (Q4_IN_VM=1, ~/.agentlab_env, hostname != parrot)" >&2
  exit 3
fi
PATTERNS=('[c]laude' '[c]odex' '[g]emini' '[q]wen' '[c]ursor-agent' '[g]oose' '[q]3-server.mjs' '[m]arker-server.mjs')
tmux kill-server 2>/dev/null
alive() { for p in "${PATTERNS[@]}"; do pgrep -u "$(id -u)" -f "$p"; done | sort -u; }
for p in "${PATTERNS[@]}"; do pkill -TERM -u "$(id -u)" -f "$p"; done
for i in $(seq 1 20); do [ -z "$(alive)" ] && break; sleep 0.5; done
if [ -n "$(alive)" ]; then
  for p in "${PATTERNS[@]}"; do pkill -KILL -u "$(id -u)" -f "$p"; done
  sleep 2
fi
left=$(alive)
if [ -n "$left" ]; then
  echo "still running:"; ps -o pid=,args= -p $(echo $left | tr ' ' ',')
  exit 1
fi
sleep 1  # let the kernel flush what the writers left
echo "clients stopped"
