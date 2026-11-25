# HKBU SCIE1007 coursework video: run Claude Code with a Gemini model (via the relay's Anthropic-style /v1/messages)
# so Gemini works as a full agent (reads/writes files, runs commands) under the same hooks and guard as Claude.
# Usage:  pwsh -File _env/gemini_cc.ps1 [claude args...]   (model: env GEMINI_CC_MODEL, default gemini-4-neon)
#   interactive:  pwsh -File _env/gemini_cc.ps1
#   headless:     pwsh -File _env/gemini_cc.ps1 -p "task..." --dangerously-skip-permissions
# The key is read from _env/keys.env (GEMINI_API_KEY) and never printed.
$Model = if ($env:GEMINI_CC_MODEL) { $env:GEMINI_CC_MODEL } else { "gemini-4-neon" }
$Rest = $args
$root = "D:/。hkbu/molecular science"
$key = (Get-Content "$root/_env/keys.env" | Where-Object { $_ -match '^\s*GEMINI_API_KEY\s*=' } | Select-Object -First 1) -replace '^\s*GEMINI_API_KEY\s*=\s*', '' -replace '^["'']|["'']$', ''
$base = ((Get-Content "$root/_env/gemini.conf" | Where-Object { $_ -match '^GEMINI_BASE_URL=' }) -replace '^GEMINI_BASE_URL=', '').Trim() -replace '/v1/?$', ''
if (-not $key -or -not $base) { Write-Error "GEMINI key or base URL missing"; exit 1 }
$env:ANTHROPIC_BASE_URL = $base
$env:ANTHROPIC_AUTH_TOKEN = $key
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
$env:ANTHROPIC_MODEL = $Model
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = $Model
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = $Model
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "gemini-4-hydrogen"
$env:CLAUDE_CODE_SUBAGENT_MODEL = $Model
$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = "1"
$env:GEMINI_AGENT = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
Set-Location $root
& claude --model $Model @Rest
exit $LASTEXITCODE
