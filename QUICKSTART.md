# 🚀 Quick Start Guide

Get started with DeepAI Banner Generator in 5 minutes!

## Prerequisites

- Python 3.11 or higher
- OpenAI API key
- DeepAI API key

## Step 1: Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd deepai_sandbox

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configuration

### Option A: Using .env file (Recommended)

```bash
# Copy the example file
cp .env.example .env

# Edit with your keys
nano .env
```

Add your API keys:

```bash
OPENAI_API_KEY=sk-your-openai-key-here
DEEPAI_API_KEY=your-deepai-key-here
```

### Option B: Using environment variables

```bash
export OPENAI_API_KEY="sk-your-openai-key"
export DEEPAI_API_KEY="your-deepai-key"
```

## Step 3: Prepare Your Content

Create a `posts/` directory with your blog posts:

```bash
mkdir -p posts
```

Add a markdown file with YAML front matter:

```markdown
---
title: "My Amazing Blog Post"
date: 2025-01-01
tags: [python, ai]
---

# Introduction

Your blog content here...
```

## Step 4: Generate Your First Banner

### Interactive Mode (Recommended)

```bash
python chain_banner.py generate
```

This will:

1. 📁 Show you all markdown files in `./posts`
2. 📖 Let you select which file to process
3. 🤖 Generate 10 creative prompts using GPT-4
4. ✨ Let you pick your favorite prompt
5. 🎨 Generate the banner via DeepAI
6. 💾 Save to `./banners/`

### Direct Mode (Quick Test)

```bash
python chain_banner.py direct "A beautiful gradient background"
```

Output saved to `banner.png`

## Step 5: Verify Output

```bash
ls -lh banners/
# or
ls -lh banner.png
```

Open the generated image in your favorite viewer!

## Common Commands

```bash
# Generate with custom dimensions
python chain_banner.py generate --width 1920 --height 600

# Use simple style (1 prompt instead of 10)
python chain_banner.py generate --style simple

# Generate HD quality
python chain_banner.py generate --version hd

# Direct mode with custom output
python chain_banner.py direct "tech banner" --output my_banner.png

# Get help
python chain_banner.py --help
python chain_banner.py generate --help
```

## Troubleshooting

### "API key not found"

Make sure your `.env` file exists and contains your keys, or export them as environment variables.

```bash
# Check if keys are set
echo $OPENAI_API_KEY
echo $DEEPAI_API_KEY
```

### "Dimensions must be multiples of 32"

DeepAI requires dimensions to be multiples of 32, between 128-1536:

✅ Valid: 512, 1024, 1536
❌ Invalid: 1000, 2000

### "No markdown files found"

Create a `posts/` directory and add `.md` files:

```bash
mkdir -p posts
echo '---
title: Test Post
---
# Test' > posts/test.md
```

### SSL Certificate Errors (macOS)

```bash
unset SSL_CERT_FILE
unset SSL_CERT_DIR
python chain_banner.py generate
```

## Next Steps

- 📖 Read the full [README.md](README.md) for advanced features
- 🔧 Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- 🧪 Run tests: `pytest`
- 🎨 Explore different prompt styles and quality settings

## Example Workflow

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Generate banner for a blog post
python chain_banner.py generate

# 3. Review generated prompts and select one

# 4. Check output
ls -lh banners/

# 5. Use the banner in your blog!
```

---

Happy banner generating! 🎉
