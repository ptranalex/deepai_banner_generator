# 🎨 DeepAI Banner Generator

Modern AI-powered banner generator for blog posts with clean architecture, type safety, and comprehensive testing.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-53%20passed-green.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen.svg)](htmlcov/)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## ✨ Features

- 🤖 **AI Prompt Generation**: Auto-generate creative banner prompts using GPT-4
- 🎨 **Two Prompt Styles**: Origami (10 prompts) or Simple (1 prompt)
- 🖼️ **DeepAI Integration**: High-quality image generation with multiple quality levels
- 📝 **Markdown Support**: Parse blog posts with YAML front matter
- 🎯 **Type-Safe**: Full type hints with mypy checking
- 🧪 **Tested**: 94% test coverage with pytest
- 🎯 **Customizable Prompts**: YAML-based prompt templates for easy tuning
- 🎭 **Beautiful CLI**: Rich terminal output with Typer
- 🔒 **Secure**: Pydantic settings, no hardcoded credentials
- 📊 **Logging**: Structured logging with Loguru

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <your-repo>
cd deepai_sandbox

# 2. Create virtual environment and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env and add your keys:
#   OPENAI_API_KEY=sk-your-key
#   DEEPAI_API_KEY=your-key

# 4. Run the tool
python chain_banner.py generate
```

## 📦 Installation

### Requirements

- Python 3.11 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- DeepAI API key ([Get one here](https://deepai.org/))

### Setup

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (for testing, linting, etc.)
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

## 🎯 Usage

### Interactive Mode (Recommended)

Generate banners with AI-powered prompt generation:

```bash
# Origami style (generates 10 creative prompts)
python chain_banner.py generate

# Simple style (generates 1 prompt)
python chain_banner.py generate --style simple

# Custom options
python chain_banner.py generate \
  --input-dir ./posts \
  --output-dir ./images \
  --style origami \
  --width 1024 \
  --height 512 \
  --version hd
```

**Workflow:**

1. 📁 Select a markdown file from your posts directory
2. 📖 Tool parses the blog post (title, tags, content)
3. 🤖 ChatGPT generates creative banner prompts
4. ✨ You select your favorite prompt
5. 🎨 DeepAI generates the banner image
6. 💾 Banner saved to output directory

### Direct Mode

Generate banners with a manual prompt (no AI chain):

```bash
# Basic usage
python chain_banner.py direct "A beautiful gradient banner"

# Custom dimensions and output
python chain_banner.py direct \
  "Modern tech banner with blue gradient" \
  --output my_banner.png \
  --width 1920 \
  --height 600 \
  --version hd
```

### Help

```bash
# Main help
python chain_banner.py --help

# Command-specific help
python chain_banner.py generate --help
python chain_banner.py direct --help
```

## ⚙️ Configuration

### Option 1: Environment Variables (Recommended)

```bash
export OPENAI_API_KEY="sk-your-openai-key"
export DEEPAI_API_KEY="your-deepai-key"
```

### Option 2: .env File

```bash
# Copy the example
cp .env.example .env

# Edit .env
nano .env
```

Example `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.9

# DeepAI Configuration
DEEPAI_API_KEY=your-deepai-key-here
DEEPAI_TIMEOUT=60

# Optional overrides
DEFAULT_INPUT_DIR=./posts
DEFAULT_OUTPUT_DIR=./banners
DEFAULT_STYLE=origami
```

### Option 3: CLI Arguments

```bash
python chain_banner.py generate \
  --openai-key "sk-..." \
  --deepai-key "..."
```

### Customizing GPT Prompts

The tool uses YAML-based prompt templates that you can customize without touching code:

```bash
# View default prompts
cat prompts.yaml

# Create local override (not tracked in git)
cp prompts.yaml prompts.local.yaml
nano prompts.local.yaml
```

Example `prompts.yaml` structure:

```yaml
simple:
  system: |
    You are a creative prompt generator...
  user: |
    Title: {title}
    Blog: {content}
    Generate one concise image prompt.

origami:
  system: |
    You are a creative image prompt generator for 3D Origamic style...
  user: |
    Title: {title}
    Full blog content: {content}
    Generate 10 creative 3D origamic prompts.
```

**Tips for tuning prompts:**

- Edit `prompts.local.yaml` to experiment without affecting version control
- Use `{title}` and `{content}` placeholders for blog post data
- Adjust system prompts to change the AI's behavior and style
- Modify user prompts to change what information is sent to GPT

## 📋 Command Reference

### Generate Command

```bash
python chain_banner.py generate [OPTIONS]
```

| Option             | Type                   | Default     | Description                              |
| ------------------ | ---------------------- | ----------- | ---------------------------------------- |
| `--input-dir, -i`  | Path                   | `./posts`   | Directory with markdown files            |
| `--output-dir, -o` | Path                   | `./banners` | Output directory for banners             |
| `--style, -s`      | `simple\|origami`      | `origami`   | Prompt generation style                  |
| `--width, -w`      | Integer                | `1024`      | Banner width (128-1536, multiple of 32)  |
| `--height, -h`     | Integer                | `512`       | Banner height (128-1536, multiple of 32) |
| `--version, -v`    | `standard\|hd\|genius` | `standard`  | DeepAI quality level                     |
| `--openai-key`     | String                 | -           | OpenAI API key                           |
| `--deepai-key`     | String                 | -           | DeepAI API key                           |

### Direct Command

```bash
python chain_banner.py direct PROMPT [OPTIONS]
```

| Argument/Option | Type                   | Default      | Description           |
| --------------- | ---------------------- | ------------ | --------------------- |
| `PROMPT`        | String                 | Required     | Text prompt for image |
| `--output, -o`  | Path                   | `banner.png` | Output file path      |
| `--width, -w`   | Integer                | `1024`       | Banner width          |
| `--height, -h`  | Integer                | `512`        | Banner height         |
| `--version, -v` | `standard\|hd\|genius` | `standard`   | Quality level         |
| `--deepai-key`  | String                 | -            | DeepAI API key        |

## 🏗️ Architecture

```
deepai_sandbox/
├── lib/                    # Core modules
│   ├── config.py          # Pydantic settings management
│   ├── logger.py          # Loguru logging setup
│   ├── gpt.py             # OpenAI GPT client
│   ├── deepai.py          # DeepAI API client
│   ├── prompts.py         # YAML prompt loader
│   └── file_handler.py    # Markdown & file operations
├── tests/                  # Pytest test suite (94% coverage)
│   ├── test_config.py
│   ├── test_gpt.py
│   ├── test_deepai.py
│   ├── test_prompts.py
│   └── test_file_handler.py
├── chain_banner.py         # Main Typer CLI
├── prompts.yaml            # GPT prompt templates
├── .env.example            # Configuration template
├── pyproject.toml          # Tool configurations
└── requirements.txt        # Production dependencies
```

### Key Design Principles

- ✅ **TDD Approach**: Tests written first, then implementation
- ✅ **Type Safety**: Full type hints, validated with mypy
- ✅ **Modular**: Clean separation of concerns
- ✅ **Testable**: 93% test coverage with mocked external APIs
- ✅ **Configurable**: Pydantic settings with validation
- ✅ **Observable**: Structured logging throughout

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lib --cov-report=html

# Run specific test file
pytest tests/test_gpt.py -v

# Run with verbose output
pytest -vv
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Type checking
mypy lib/
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 📝 Markdown File Format

Blog posts should be markdown files with YAML front matter:

```markdown
---
title: "Your Blog Post Title"
date: 2025-01-01
tags: [python, ai, tutorial]
categories: [Tech, Programming]
---

# Your Content

Your blog post content here...
```

## 🔧 Troubleshooting

### SSL Certificate Errors

If you encounter SSL certificate errors on macOS:

```bash
# Check your SSL_CERT_FILE
echo $SSL_CERT_FILE

# If it points to a non-existent file, unset it
unset SSL_CERT_FILE
unset SSL_CERT_DIR
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

### API Key Issues

```bash
# Verify keys are set
echo $OPENAI_API_KEY
echo $DEEPAI_API_KEY

# Or check .env file
cat .env
```

### Dimension Validation

DeepAI requires dimensions to be:

- Multiples of 32
- Between 128 and 1536 pixels

Valid examples: 512, 1024, 1536
Invalid examples: 1000, 2000

## 📊 Test Coverage

Current test coverage: **94%**

```
Name                  Stmts   Miss  Cover
-------------------------------------------
lib/config.py            31      0   100%
lib/deepai.py            56      7    88%
lib/file_handler.py      48      5    90%
lib/gpt.py               63      3    95%
lib/logger.py             9      0   100%
lib/prompts.py           51      3    94%
-------------------------------------------
TOTAL                   293     19    94%
```

## 🛠️ Tech Stack

- **CLI Framework**: [Typer](https://typer.tiangolo.com/) - Modern Python CLI
- **Configuration**: [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Type-safe config
- **Logging**: [Loguru](https://github.com/Delgan/loguru) - Simple, powerful logging
- **Testing**: [Pytest](https://pytest.org/) - Full test suite with fixtures and mocks
- **Code Quality**: [Ruff](https://github.com/astral-sh/ruff) - Fast linter & formatter
- **Type Checking**: [Mypy](https://mypy-lang.org/) - Static type checker
- **Terminal UI**: [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- **AI APIs**: OpenAI GPT-4o & DeepAI text2img

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests first (TDD approach)
4. Implement your feature
5. Ensure all tests pass: `pytest`
6. Ensure code quality: `ruff check . && mypy lib/`
7. Submit a pull request

## 📄 License

This project is provided as-is for generating banner images using DeepAI and OpenAI APIs.

## 🔗 Links

- [DeepAI API Documentation](https://deepai.org/machine-learning-model/text2img)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Made with ❤️ using TDD principles and modern Python best practices**
