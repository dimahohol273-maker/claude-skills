@echo off
setlocal

REM ====== НАСТРОЙКИ ======
REM Вставь сюда свой ключ OmniRoute
set "ANTHROPIC_AUTH_TOKEN=sk-0ad55b917d22092e-f440c2-c599fd58

REM Вставь сюда Anthropic-compatible endpoint OmniRoute
REM Пример: https://api.omniroute.ai
set "ANTHROPIC_BASE_URL=http://localhost:20128/v1

REM Опционально: если gateway не любит experimental betas
set "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1"

REM Опционально: модель, если твой gateway требует явное имя
 set "ANTHROPIC_MODEL=kr/claude-sonnet-4.5

echo Starting Claude Code via OmniRoute...
claude

endlocal