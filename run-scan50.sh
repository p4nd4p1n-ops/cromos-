#!/bin/bash
# run-scan50.sh — lanza comc-scan50 con auto-reinicio hasta OK completo o bloqueo persistente.
# Se relanza solo si el script se cae (exit != 0) sin bloqueo; con bloqueo espera 15 min y reintenta (máx 3).
set -u
LOG=/root/comc-data/scan50-run.log
BLOQUEOS=0
for i in 1 2 3 4 5 6 7 8 9 10; do
  echo "=== intento $i $(date) ===" >> "$LOG"
  python3 /root/comc-scripts/comc-scan50.py >> "$LOG" 2>&1
  RC=$?
  if [ $RC -eq 0 ]; then
    echo "OK COMPLETO $(date)" >> "$LOG"
    exit 0
  fi
  if [ $RC -eq 3 ]; then
    BLOQUEOS=$((BLOQUEOS+1))
    if [ $BLOQUEOS -ge 3 ]; then
      echo "3 BLOQUEOS SEGUIDOS — PARO DEFINITIVO $(date)" >> "$LOG"
      exit 9
    fi
    echo "BLOQUEO $BLOQUEOS/3 — espera 15 min $(date)" >> "$LOG"
    sleep 900
  else
    echo "error RC=$RC — espera 2 min $(date)" >> "$LOG"
    sleep 120
  fi
done
echo "AGOTADO 10 INTENTOS $(date)" >> "$LOG"
exit 10
