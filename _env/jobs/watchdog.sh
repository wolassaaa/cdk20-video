#!/bin/bash
# HKBU SCIE1007 coursework video: keeps the overnight jobs alive until 23:00 (director games after 23:00, GPU must be free) Korea time. Started by Windows Task
# Scheduler, so an Orca restart does not stop it or the jobs it starts. Every 2 minutes: a job whose log has no
# "== 全部结束" and that is not running is started again (finished pieces are skipped by the jobs themselves).
cd "D:/。hkbu/molecular science/_env/jobs" || exit 1
JOBS="edges c_audio stage3 board"
running() { powershell.exe -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"name='bash.exe'\" | Where-Object { \$_.CommandLine -like '*$1.sh*' }).Count" | tr -d '\r'; }
while [ "$(date +%H%M)" -lt 2300 ]; do
  for j in $JOBS; do
    if [ "$j" != board ] && grep -q "== 全部结束" "$j.log" 2>/dev/null; then continue; fi
    if [ "$(running $j)" = 0 ]; then
      echo "$(date +%T) 拉起 $j" >> watchdog.log
      [ "$j" = board ] && { bash board.sh > /dev/null 2>&1 & } || { bash "$j.sh" >> "$j.log" 2>&1 & }
    fi
  done
  if [ ! -f "../../镜头设计_v3/粗剪/粗剪检查.md" ] && [ "$(running glm_cut)" = 0 ] && ! grep -q "^log:" glm_cut.log 2>/dev/null; then
    echo "$(date +%T) 拉起 glm_cut" >> watchdog.log; bash glm_cut.sh >> glm_cut.log 2>&1 &
  fi
  sleep 120
done
echo "$(date +%T) 看门狗到点结束" >> watchdog.log
