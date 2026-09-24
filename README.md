# APEX: Engineering Intelligence System

> Personal intelligence radar for **Electronics, Embedded Systems, Drones, Robotics, Edge AI, FPGA, and Open Hardware**. Scans arXiv and GitHub daily, scores everything, kills the noise, and delivers a formatted newsletter to this repo every week.

---

## Latest Reports

| Report | Date |
|:---|:---|
| [Weekly Report](projects/) | Check `projects/` for all weekly and daily reports |

Reports are auto-published to this repo as Markdown. Open any report file — GitHub renders it beautifully.

---

## What APEX Does

```
arXiv papers + GitHub repos + ecosystem releases
        │
        ▼
    SCORE (7 dimensions: relevance, actionability, depth, novelty, source quality, hw compat, learning)
        │
        ▼
    FILTER (LLM slop → killed, web dev/crypto → killed, hype language → penalized)
        │
        ▼
    REPORT
    ├── Top Discoveries (scored & ranked)
    ├── Research Papers (arXiv, domain-matched)
    ├── Electronics & Hardware
    ├── Drones & Robotics
    ├── AI + Hardware (TinyML, edge inference — NOT chatbot wrappers)
    ├── Engineering Opportunities (BUILD NOW / BUILD WITH ADDITIONS)
    ├── What I Should Learn
    ├── VP DEMO CORNER (open-source projects for club events & shows)
    └── IF I ONLY HAVE 5 HOURS THIS WEEK
```

---

## Domains Tracked

- **Embedded**: ESP32, STM32, RP2040, Zephyr, FreeRTOS, bare-metal firmware
- **Drones/UAV**: PX4, ArduPilot, Betaflight, MAVLink, FPV, swarm, flight controllers
- **Robotics**: SLAM, navigation, motor control (BLDC/FOC), ROS 2, simulation
- **Edge AI**: TinyML, quantized inference, ONNX, TFLite, CMSIS-NN, object detection on-device
- **FPGA/HDL**: Verilog, VHDL, RISC-V, open silicon, accelerators
- **RF/Comms**: SDR, wireless protocols, mesh networks, antenna design
- **Open Hardware**: PCB/KiCad, open-source hardware, sensors, power electronics, BMS
- **Research**: arXiv CS.RO, CS.AI, EE.SP, EE.SY, CS.CV — filtered to hardware-relevant papers only

---

## Scoring Philosophy

| Principle | What it means |
|:---|:---|
| **SIGNAL > VOLUME** | 5 useful items beat 50 random links |
| **USEFULNESS > POPULARITY** | Stars don't matter if you can't use it |
| **PRIMARY SOURCES > NEWS** | Papers and repos, not blog rewrites |
| **ACTIONABILITY > HYPE** | "Can I build this?" beats "this is revolutionary" |
| **NEW INFORMATION > DUPLICATES** | Fuzzy title dedup (Jaccard 0.70) kills repeats |

### What gets killed automatically
- ChatGPT/LLM wrappers, LangChain apps, prompt engineering repos
- Web dev frameworks, React components, WordPress plugins
- Crypto/blockchain/NFT/Web3
- Marketing tools, SEO, e-commerce
- Projects requiring H100/A100/DGX (flagged as FUTURE, not shown)

---

## CLI

```bash
# Live scan of arXiv + GitHub
python -m apex.cli scan --limit 5

# Generate and auto-publish daily report
python -m apex.cli daily

# Generate and auto-publish weekly report
python -m apex.cli weekly

# Scaffold embedded project templates
python -m apex.cli scaffold esp32_p4_vision
python -m apex.cli scaffold ros2_px4_offboard
python -m apex.cli scaffold simplefoc_bldc

# Audit text for AI cliches (humanizer)
python -m apex.cli humanize ./draft.md

# Compress compiler logs (context-mode)
python -m apex.cli filter-logs ./build_output.log
```

---

## Architecture

```
apex/
├── intelligence/
│   ├── arxiv_radar.py      # 5 category + 8 keyword arXiv queries
│   ├── github_radar.py     # v4: 14 concept-driven NEW + 4 TRENDING + 17 release monitors
│   └── scoring.py          # 7-dimension scorer, LLM slop filter, hardware profile
├── memory/
│   └── store.py            # 30-column SQLite, fuzzy dedup, trend snapshots
├── reporting/
│   ├── daily.py            # Daily digest with quality gate
│   ├── weekly.py           # 13-section weekly report + VP Demo Corner
│   └── telegram.py         # Optional Telegram push
├── engineering/
│   └── scaffolds.py        # ESP32, ROS 2, SimpleFOC project templates
├── content/
│   └── humanizer.py        # AI cliche detector and cleaner
├── utils/
│   ├── context_filter.py   # GCC/ROS2 log compressor
│   └── worktree_mgr.py     # Git worktree manager
└── cli.py                  # Unified CLI with auto-publish to GitHub
```

### Integrated Upstream Engines

| Engine | Source | Purpose |
|:---|:---|:---|
| Communication Core | [i-have-adhd](https://github.com/ayghri/i-have-adhd) | Action-first, zero-fluff output |
| Humanizer | [humanizer](https://github.com/blader/humanizer) | Strips AI cliches from text |
| Engineering Rigor | [ECC](https://github.com/affaan-m/ECC) | TDD and hardware-first verification |
| Context Optimizer | [context-mode](https://github.com/mksglu/context-mode) | Compresses compiler logs 98% |
| Workspace Sandbox | [worktrunk](https://github.com/max-sixty/worktrunk) | Isolated Git worktrees |
| Research Radar | [Agent-Reach](https://github.com/Panniantong/Agent-Reach) | Multi-source intelligence scraper |

---

## Hardware Profile

Scoring is personalized to what you actually own:

| Component | Value |
|:---|:---|
| GPU | RTX 3050 (4GB VRAM) |
| RAM | 16GB |
| Boards | Raspberry Pi, Arduino, ESP32 |
| Tools | PlatformIO, Arduino IDE, KiCad |
| Simulator | Gazebo |
| Budget | Student |

Edit `~/.apex/profile.json` to update.

---

*Built by Siddhant Rahate ([@25sidhx](https://github.com/25sidhx)) — VP, Drone & Robotics Club*
