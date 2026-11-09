@echo off
rem Start the local Agent Mail server (127.0.0.1:8765) for Claude / DS / Codex.
curl -sf http://127.0.0.1:8765/health/liveness >nul 2>&1
if not errorlevel 1 (
  echo Agent Mail already running: http://127.0.0.1:8765/mail/
  goto :eof
)
if not exist "%USERPROFILE%\.local\share\mcp-agent-mail\git_mailbox_repo" mkdir "%USERPROFILE%\.local\share\mcp-agent-mail\git_mailbox_repo"
start "Agent Mail" /min "%USERPROFILE%\.local\bin\mcp-agent-mail.exe" serve --no-tui
echo Agent Mail started: http://127.0.0.1:8765/mail/
