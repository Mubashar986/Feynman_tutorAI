# Developer Environment & Prerequisites Guide
## AI-Powered Adaptive Exam Learning Platform

**Document Version:** 1.0  
**Target Audience:** Developers, New Team Members, AI Agents  
**Core Philosophy:** **Local-First & Zero-Setup by Default** with flexible Multi-Provider support.

---

## 1. The Zero-Setup Local Guarantee

When a developer clones this repository, **they do not need to install complex local databases, configure cloud credentials, or spend money on subscriptions** to start development and run unit tests.

| Service Domain | Zero-Setup Local Mode (Default) | Production / Cloud Mode (Optional) |
| :--- | :--- | :--- |
| **Relational Database** | Local SQLite (`data/app.db`) — **0 setup, 0 passwords** | PostgreSQL on Supabase / Neon / Docker |
| **Vector Database** | Qdrant local disk (`data/vector_db`) — **0 setup, 0 API keys** | Qdrant Cloud / Remote Cluster |
| **Caching / Queue** | In-memory fallback — **0 setup** | Redis Server + ARQ Worker |
| **Object Storage** | Local folder (`data/uploads/`) — **0 setup** | AWS S3 / Cloudflare R2 / MinIO |
| **AI / LLMs** | Local Ollama ($0) OR Free OpenRouter / Groq | Paid Claude / GPT-4o / Gemini / Grok |

---

## 2. Multi-Provider AI Credentials Directory

To run live AI generation features (Question Laboratory, Socratic Tutor, Teach-Back grading), configure **at least ONE** provider in your `.env` file. You have total freedom to pick whatever is fastest or free:

### Option A: OpenRouter (Recommended — Multi-Model Aggregator)
* **Why it's great:** 1 single API key gives you access to DeepSeek R1, Llama 3.3, Claude 3.5, and GPT-4o with many free-tier models.
* **Get API Key:** [https://openrouter.ai/keys](https://openrouter.ai/keys)
* **Variable in `.env`:** `OPENROUTER_API_KEY="sk-or-v1-..."`
* **Default Model:** `meta-llama/llama-3.3-70b-instruct` or `deepseek/deepseek-r1`

---

### Option B: Groq Cloud (Ultra-Fast 500 T/s Free Tier)
* **Why it's great:** Extremely fast inference speed for real-time Socratic dialogue with a generous free tier.
* **Get API Key:** [https://console.groq.com/keys](https://console.groq.com/keys)
* **Variable in `.env`:** `GROQ_API_KEY="gsk_..."`
* **Default Model:** `llama-3.3-70b-versatile` or `mixtral-8x7b-32768`

---

### Option C: Local Ollama (100% Free, Offline, Zero API Keys)
* **Why it's great:** Runs models locally on your GPU/CPU with $0 cost and zero cloud dependencies.
* **Download & Install:** [https://ollama.com](https://ollama.com)
* **Run Model:**
  ```powershell
  ollama run llama3.1
  # or
  ollama run qwen2.5
  ```
* **Variable in `.env`:** `OLLAMA_BASE_URL="http://localhost:11434"`

---

### Option D: Direct Commercial & Specialized Providers
If you already have active credits with a specific provider:
* **xAI / Grok:** [https://console.x.ai/](https://console.x.ai/) → `XAI_API_KEY="..."`
* **DeepSeek (Direct):** [https://platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) → `DEEPSEEK_API_KEY="..."`
* **Together AI:** [https://api.together.xyz/settings/api-keys](https://api.together.xyz/settings/api-keys) → `TOGETHER_API_KEY="..."`
* **OpenAI:** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) → `OPENAI_API_KEY="..."`
* **Anthropic:** [https://console.anthropic.com/](https://console.anthropic.com/) → `ANTHROPIC_API_KEY="..."`
* **Google Gemini:** [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) → `GEMINI_API_KEY="..."`

---

## 3. The Universal Developer Action Card Protocol

Whenever an AI Agent (or human developer) begins a task that depends on unconfigured credentials or services, the agent MUST output this standardized Action Card:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔑 DEVELOPER PREREQUISITE ACTION REQUIRED                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. WHAT IS NEEDED:        [Component name, e.g. LLM API / S3 Storage / DB]  │
│ 2. WHY IT IS NEEDED:      [Which WBS task / feature requires this]          │
│ 3. WHERE TO GET IT (URLs):                                                  │
│    • Free / Fastest Option: [Portal URL + 1-minute signup instructions]     │
│    • Aggregator / Multi:    [Portal URL, e.g. OpenRouter]                   │
│    • 100% Free / Offline:   [Download URL for local tool, e.g. Ollama]      │
│    • Standard / Enterprise: [Official vendor portal URL]                    │
│ 4. WHERE TO PUT IT:       [Exact file: .env]                                │
│    • Exact Variable Name:   KEY_NAME=your_value_here                        │
│ 5. ZERO-SETUP FALLBACK:   [Explain how to run with local mock if skipped]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Quick Start: 30-Second Setup for New Developers

```powershell
# 1. Copy the environment template
cp .env.example .env

# 2. (Optional) Paste your preferred LLM key into .env
# e.g. OPENROUTER_API_KEY="sk-or-v1-..." or GROQ_API_KEY="gsk_..."

# 3. Run backend tests to verify environment
pytest backend/tests/test_health.py -v
```
