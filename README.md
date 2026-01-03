## 🦊 Kirana

> **"Kirana, a good child born on Monday, October 19, 2015"**

Kirana is a hybrid AI-based cybersecurity assistant combining local and external intelligence. Built with a **"Dual Persona"** architecture and empowered by a dual hybrid brain:

- **Kirana (Blue Team):** Professional, Analytical and Reporting Expert. Your CISO.
- **Yayuk (Red Team):** Savage, Uncensored and Coding Expert. Your Bad Girl Hacker.

---

## ✨ Key Features

### 🎭 Dual Persona Architecture

[](https://github.com/ajobondon/kirana-OLD#-dual-persona-architecture)

- 😇 **Kirana (Blue Team):** She's your CISO.
- 😈 **Yayuk (Red Team):** Your bad girl hacker.

### 🧠 Quad-Core Intelligence (4 Wings)

[](https://github.com/ajobondon/kirana-OLD#-quad-core-intelligence-4-wings)

- 👩🏻‍💻 **Blue Core 1** Kirana's main brain (Analytical & Reasoning).
- 👩‍💻 **Blue Core 2** High-speed backup brain.
- 🥷 **Red Core 1** Yayuk's main brain (Superior Coding Logic).
- 👤 **Red Core 2:** Yayuk's backup brain (Fallback).

### 🛡️ Forensic & Security Operations

[](https://github.com/ajobondon/kirana-OLD#%EF%B8%8F-forensic--security-operations)

- 👁️ **Autonomous Security Intelligence:** Total transformation from a reactive assistant to a proactive guardian! This subsystem runs 24/7 to audit server health and security, then performs reporting via **Telegram Push Notification** when anomalies are detected.
- 🔬 **Forensic Safe-Stream:** Combines _Error Hunting_ and _Contextual Tail_ in real-time.
- 🔓 **Smart Jailbreak Context:** Anti-LLM sensor (uses _Educational Context_).
- 🔎 **Log Sentinel:** Log forensics automation that hunts attack patterns and presents an instant Executive Summary + Mitigation Plan.

### ⚙️ Advanced System Control

[](https://github.com/ajobondon/kirana-OLD#%EF%B8%8F-advanced-system-control)

- 🎛️ **Interactive Neural Selector:** Full control in your hands. Choose specific AI brains for every heavy analysis task as needed.
- 🔀 **Auto-Failover Matrix:** One brain down? The system automatically switches tasks to a backup brain without downtime.
- 🚑 **Self-Healing Code:** Typo or logic error? Doctor Yayuk can dissect broken files, fix syntax, and even perform autonomous code refactoring.
- ⚡ **Dumb Pipe Execution:** Execute heavy tools in Real-Time directly to the terminal without AI latency.

### 🌐 Connectivity & Memory

[](https://github.com/ajobondon/kirana-OLD#-connectivity--memory)

- 🧠 **Auto-RAG (Dynamic Learning):** _Evolving Memory_ that can be taught new tricks instantly. Just say _"Remember this"_, and the solution will be permanently saved to _Experience Memory_. Supports _Learn_ & _Forget_ features.
- 🔔 **Kirana Reminder:** Your personal timekeeper. Tell Kirana to schedule tasks using natural language ("Remind me to check logs in 10 mins"), and she will alert you via Telegram right on time.
- 🌐 **Real-Time Internet:** Connected to search engines for latest data validation (recent CVEs, Exploit DB).
- ⏱️ **Ephemeral Context:** Smart short-term memory in One-Shot CLI mode to maintain context without hallucinations.
- 📖 **Knowledge Base:** Private RAG database to store "muscle memory" and team SOPs.
- 📱 **Kirana Telegram:** Let's hack on the road!
    

---

## ⚙️ Installation

### 1. Prerequisites

- OS: Ubuntu / Debian / WSL2 / RedHat Based.
    
- Python 3.11+.
    
- Connection to **Kirana Server** (IP/Domain).
    

### 2. Setup Project

Bash

```
# 1. Clone Repository
git clone https://github.com/ajobondon/kirana.git ~/kirana

# 2. Enter Directory
cd ~/kirana

# 3. Create Virtual Environment
python3 -m venv env

# 4. Activate & Install Dependencies
source env/bin/activate
pip install -r requirements.txt
```

### 3. Configuration (.env)

Create a `.env` file in the `~/kirana/` folder:

TOML

```
# Target Server
KIRANA_SERVER_URL="https://ayala.palawamaya.com"

# Client Identity
CLIENT_ID="<YOUR_ID>"

# --- API KEY ---
# Request Key from: kirana@palawamaya.com
X_API_KEY="<KIRANA_API_KEY>"

# Local Workspace
WORKSPACE_DIR="~/kirana/workspace"
```

---

## ⚡ Terminal Integration (Required)

To fully integrate Kirana with your Linux shell (enabling global access & Magic Fallback), you **MUST** update your bash configuration.

1. Open your `.bashrc` file:
    
    Bash
    
    ```
    nano ~/.bashrc
    ```
    
2. Scroll to the bottom and **Paste** the following code:
    

Bash

```
# =========
# 🦊 KIRANA
# =========

# 1. Define Global Variables
export KIRANA_HOME="$HOME/kirana"
export KIRANA_PYTHON="$KIRANA_HOME/env/bin/python"
export KIRANA_SCRIPT="$KIRANA_HOME/kirana.py"

# 2. Main Function (Chat & One-Shot)
# Usage: 'kirana' (chat loop) or 'kirana <cmd>' (one-shot)
kirana() {
    if [ $# -eq 0 ]; then
        # Interactive Chat Mode
        PYTHONWARNINGS="ignore" $KIRANA_PYTHON $KIRANA_SCRIPT
    else
        # Explicit One-Shot Mode
        PYTHONWARNINGS="ignore" $KIRANA_PYTHON $KIRANA_SCRIPT "$*"
    fi
}

# Helper Aliases
alias help="kirana help"
alias tanya="kirana"

# 3. Magic Fallback (AI Shell)
# Catches command errors/typos and asks Kirana for help.
command_not_found_handle() {
    local cmd="$*"
    
    # Safety Check: Do not process empty commands
    if [ -z "$cmd" ]; then return 127; fi
    
    # Safety Check: Do not process relative/absolute paths (let standard errors flow)
    if [[ "$cmd" == ./* ]] || [[ "$cmd" == /* ]]; then
        printf "bash: %s: No such file or directory\n" "$cmd"
        return 127
    fi

    # Throw to Kirana (Silent Mode)
    PYTHONWARNINGS="ignore" $KIRANA_PYTHON $KIRANA_SCRIPT "$cmd"
    
    return 0
}
```

3. Save and Reload:
    
    Bash
    
    ```
    source ~/.bashrc
    ```
    

---

## 📖 Usage Guide

### 1. Interactive Mode

Type `kirana` in the terminal to enter a continuous chat session.

Plaintext

```
Fox 🦊: Create a python calculator script
...
Fox 🦊: exit
```

### 2. Just chat her

Type what ever you want for quick execution without entering chat mode.

- **Check News:** `berita viral hari ini`
    
- **System Check:** `cek system`
    
- **Morning Patrol:** `patroli`
    
- **Security Scan:** `cek keamanan <TARGET>`
    

### 3. Magic Fallback (AI Shell)

If you mistype a Linux command or forget how to perform a task, just type what you think. Kirana will catch the error.

Bash

```
# Example: You forgot how to extract a tar.gz file
user@laptop:~$ cara extract file archive.tar.gz

# Kirana will automatically appear and provide the solution:
# "Use command: tar -xzvf archive.tar.gz"
```

---

## ⚠️ Disclaimer

This application includes capabilities for running _Security Scanning_ and _System Updates_. Use wisely and responsibly. Do not use scanning features on targets you do not own or have permission to test.

**Any inquiry:** 📧 `kirana@palawamaya.com`

---

_© 2026 Kirana Ecosystem._