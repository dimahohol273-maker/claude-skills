# Claude Code Skills

Коллекция пользовательских скиллов для Claude Code.

## 📥 Установка скиллов

### Вариант 1: Скачать один скилл

```bash
# Перейти в директорию скиллов
cd ~/.claude/skills

# Скачать конкретный скилл
curl -O https://raw.githubusercontent.com/dimahohol273-maker/claude-skills/master/.claude/skills/example-skill.md
```

### Вариант 2: Клонировать весь репозиторий

```bash
# Клонировать репозиторий
git clone https://github.com/dimahohol273-maker/claude-skills.git

# Скопировать скиллы
cp -r claude-skills/.claude/skills/* ~/.claude/skills/
```

### Вариант 3: Прямая ссылка (Windows)

```powershell
# Скачать в директорию скиллов Claude
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/dimahohol273-maker/claude-skills/master/.claude/skills/example-skill.md" -OutFile "$env:USERPROFILE\.claude\skills\example-skill.md"
```

## 📂 Структура

```
.claude/skills/
├── example-skill.md        # Пример структуры скилла
└── README.md              # Эта инструкция
```

## ✨ Как использовать

После установки скиллы автоматически доступны в Claude Code:

```
/example    # Вызвать скилл напрямую
```

Или Claude загрузит скилл автоматически по триггерным словам.

## 🛠️ Создание своих скиллов

1. Создайте файл `.md` в `.claude/skills/`
2. Добавьте frontmatter с метаданными:
   ```markdown
   ---
   name: my-skill
   description: What this skill does
   triggers:
     - "keyword1"
     - "keyword2"
   ---
   ```
3. Опишите инструкции для Claude

## 📚 Доступные скиллы

- **example-skill** - Пример структуры скилла

## 🔗 Ссылки

- [GitHub Repository](https://github.com/dimahohol273-maker/claude-skills)
- [Claude Code Documentation](https://docs.anthropic.com/claude/docs)
