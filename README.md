# ProjectChronosBot

ProjectChronosBot is an advanced AI-powered Discord bot designed to streamline server management, enhance moderation, and engage communities with intelligent features. It leverages natural language understanding and slash commands to provide a seamless and powerful user experience.

## 🚀 Features

### 🤖 AI-Powered Interaction

- Natural language command processing via an integrated AI agent
- Legacy command support with `¬askai` prefix
- Slash command interface for modern Discord UX

### 🛠️ Server Management Tools

- List, create, and delete channels with safety confirmations
- Manage roles: assign, remove, and validate permissions
- Cross-server cloning and server reset/restore capabilities

### 🧹 Moderation Suite

- Word filtering with configurable actions: delete, warn, timeout, kick
- Anti-spam detection and mitigation
- Timeout and ban automation for rule enforcement

### 🎉 Fun & Engagement

- Create interactive polls with emoji-based voting
- Timed poll results with automatic summary
- Customizable durations and options

### 🔐 Safety & Control

- Confirmation required for dangerous operations (e.g., delete all channels)
- Owner and whitelist-based command access
- Session tracking for contextual awareness

## 🧪 Testing & Validation

- Extensive test suite for all bot features
- Live and simulated test environments
- Validation scripts for schema and API integration

## 🛠️ Setup & Hosting

### Environment Configuration

To run this bot, you must define your own environment variables. These are not included in the codebase and must be set manually:

- `DISCORD_BOT_TOKEN` — your bot's token
- `OPENAI_API_KEY` — for OpenAI-compatible models
- `GOOGLE_API_KEY` — for Google AI models
- `OPENROUTER_API_KEY` — for OpenRouter access

These are optional and can be customized per user. The bot will automatically detect and use whichever keys are provided.

### Hosting

- `keep_alive.py` for persistent hosting (e.g., Replit)
- Hosting guide included in `project_docs/KEEP_ALIVE_AND_HOSTING_GUIDE.md`

## 📄 Documentation

- All documentation has been moved to the `project_docs/` folder
- Includes:
  - `COMPLETE_COMMAND_REFERENCE.md`
  - `DISCORD_INTERACTION_AND_API_FIXES.md`
  - `FIXES_APPLIED.md`
  - and more...

## 📦 Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## 🧠 Powered By

- `discord.py` for bot framework
- Custom AI agent for natural language understanding
- Modular architecture for easy extension

---

## 🛡️ License

MIT License
