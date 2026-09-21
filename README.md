# 🛰️ APEX: Autonomous Tech Intelligence & Embedded Engineering System

> **A high-signal, zero-fluff intelligence and rapid prototyping harness for Electronics & Telecommunication engineering, embedded systems, robotics, and drone development.**

---

## ⚡ Architecture & Integration

APEX fuses 6 open-source agent workflow engines into an automated engineering powerhouse:

| Engine / Component | Upstream Source | Purpose in APEX |
| :--- | :--- | :--- |
| **Communication Core** | [`ayghri/i-have-adhd`](https://github.com/ayghri/i-have-adhd) | Action-first, numbered technical execution; zero conversational fluff. |
| **Voice & Prose Refiner** | [`blader/humanizer`](https://github.com/blader/humanizer) | Strips AI cliches; ensures authentic human cadence for papers and content. |
| **Engineering Rigor** | [`affaan-m/ECC`](https://github.com/affaan-m/ECC) | TDD, register checking, memory safety, and hardware targeting instincts. |
| **Context Optimizer** | [`mksglu/context-mode`](https://github.com/mksglu/context-mode) | Compresses multi-thousand line compiler logs (GCC/ROS2) by up to 98%. |
| **Workspace Sandbox** | [`max-sixty/worktrunk`](https://github.com/max-sixty/worktrunk) | Isolated Git worktree manager for concurrent agent tasks. |
| **Research Radar** | [`Panniantong/Agent-Reach`](https://github.com/Panniantong/Agent-Reach) | Multi-source scraper and ranker for arXiv, GitHub, and hardware ecosystems. |

---

## 🚀 Quickstart CLI Commands

```bash
# 1. Run live research radar scan across arXiv and GitHub
python -m apex.cli scan --limit 5

# 2. Scaffold a hardware/robotics template
python -m apex.cli scaffold esp32_p4_vision --output-dir ./projects/p4_vision
python -m apex.cli scaffold ros2_px4_offboard --output-dir ./projects/px4_offboard
python -m apex.cli scaffold simplefoc_bldc --output-dir ./projects/bldc_controller

# 3. Audit and clean paper drafts or posts for AI cliches
python -m apex.cli humanize ./draft.md

# 4. Compress massive compiler logs before feeding to LLM
python -m apex.cli filter-logs ./build_output.log

# 5. List active Git worktree branches
python -m apex.cli worktrees
```

---

## 📂 Project Structure

```
calm-salk/
├── pyproject.toml
├── README.md
├── AGENTS.md                  # Active operational protocols
├── .agents/
│   └── skills/
│       └── embedded-harness/  # Zero-fluff TDD embedded engineering skill
├── apex/
│   ├── cli.py                 # Unified CLI application
│   ├── intelligence/          # arXiv & GitHub research radar
│   ├── engineering/           # Deterministic hardware scaffolds
│   ├── content/               # Humanizer and technical content generators
│   └── utils/                 # Context filter & Git worktree manager
└── projects/                  # Generated firmware & ROS 2 packages
```

---

*Engineered by Siddhant Rahate (`25sidhx`) · Autonomous Technology Intelligence*
## 📰 Viewing the Newsletter & Telegram Notifications

APEX v2.0 generates high-signal daily and weekly intelligence reports ("newsletters") with engineering translation (*"Why should I care?"*, *"Can I use it?"*).

### Telegram Setup
To get reports sent directly to your phone via Telegram:
1. Message **@BotFather** on Telegram and create a new bot (/newbot).
2. Copy the **Bot Token**.
3. Send a message to your new bot.
4. Go to https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates to find your chat_id.
5. Add them to ~/.apex/profile.json:
\\\json
{
  "hardware": { ... },
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  }
}
\\\
6. Run the reporter with the --telegram flag:
   \\\ash
   python -m apex.cli weekly --telegram
   python -m apex.cli daily --telegram
   \\\

### GitHub Web View
All reports are saved as Markdown in the \projects/\ directory. You can easily view them beautifully formatted on GitHub by navigating to this repository in your browser.
