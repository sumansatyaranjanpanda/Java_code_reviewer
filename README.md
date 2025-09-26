---![80d05753cf0eb0ecd15bbcb6e7235265a59392d972c0416bd3b944f0](https://github.com/user-attachments/assets/b75d134a-9400-4990-878a-4af22c512453)


## Table of Contents

- [Project Overview](#project-overview)  
- [Features](#features)  
- [Architecture](#architecture)  
- [Files of interest](#files-of-interest)  
- [Getting started (local)](#getting-started-local)  
- [Environment variables](#environment-variables)  
- [Usage](#usage)  
- [Example input & final updated code](#example-input--final-updated-code)  
- [Testing & dev tips](#testing--dev-tips)  
- [Limitations](#limitations)  
- [Future work](#future-work)  
- [License](#license)

---

## Project Overview

This project explores how to structure a small, auditable system that uses LLMs to assist in code reviews. Instead of asking a single LLM for open-ended recommendations, the system splits the job into 10 narrow, focused guideline checks, merges the outputs deterministically, and asks a final transformer to apply the consolidated changes.

The system is intended for demonstration and educational purposes — it is not a production-ready code fixer.

---

## Features

- Runs **10 guideline agents** in parallel (fan-out), merges results (fan-in), then applies an integrated patch.
- Produces a **Final Updated Java file** with an applied guideline header (e.g., `/* Applied: G01,G02,... */`).
- **Streamlit UI** for quick demos — paste or upload `.java` files and download results.
- **Stub mode** for deterministic offline testing.
- Truncation and token caps to avoid runaway LLM requests.

---
START
├─ G01_node
├─ G02_node
├─ ...
└─ G10_node
↓
MERGE (llm_node) -> consolidated suggestions
↓
FINAL_TRANSFORMER -> updated Java file
↓
END



Key components:
- `app.py` — Streamlit frontend and entry point.
- `core/graph.py` — workflow assembly (fan-out / fan-in).
- `core/node.py` — guideline prompt builders, merger logic, final transformer.
- `core/clients.py` — LLM wrapper and normalization layer.
- `core/schema.py` — Pydantic model(s) for structured state.

---

## Files of interest

- `app.py` — UI and orchestration trigger.  
- `core/graph.py` — builds the multi-agent graph.  
- `core/node.py` — main prompt logic, merging rules, final patching.  
- `core/clients.py` — LLM adapter (retries, stubs).  
- `core/schema.py` — typed state model.  
- `MultiAgent_Java_Reviewer_Report_with_Code.pptx` — presentation included in the repo (if provided).

---

## Getting started (local)

1. Clone this repo:
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>

Key components:
- `app.py` — Streamlit frontend and entry point.
- `core/graph.py` — workflow assembly (fan-out / fan-in).
- `core/node.py` — guideline prompt builders, merger logic, final transformer.
- `core/clients.py` — LLM wrapper and normalization layer.
- `core/schema.py` — Pydantic model(s) for structured state.

---

## Files of interest

- `app.py` — UI and orchestration trigger.  
- `core/graph.py` — builds the multi-agent graph.  
- `core/node.py` — main prompt logic, merging rules, final patching.  
- `core/clients.py` — LLM adapter (retries, stubs).  
- `core/schema.py` — typed state model.  
- `MultiAgent_Java_Reviewer_Report_with_Code.pptx` — presentation included in the repo (if provided).

---

## Getting started (local)

1. Clone this repo:
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>

Key components:
- `app.py` — Streamlit frontend and entry point.
- `core/graph.py` — workflow assembly (fan-out / fan-in).
- `core/node.py` — guideline prompt builders, merger logic, final transformer.
- `core/clients.py` — LLM wrapper and normalization layer.
- `core/schema.py` — Pydantic model(s) for structured state.

---

## Files of interest

- `app.py` — UI and orchestration trigger.  
- `core/graph.py` — builds the multi-agent graph.  
- `core/node.py` — main prompt logic, merging rules, final patching.  
- `core/clients.py` — LLM adapter (retries, stubs).  
- `core/schema.py` — typed state model.  
- `MultiAgent_Java_Reviewer_Report_with_Code.pptx` — presentation included in the repo (if provided).

---

## Getting started (local)

1. Clone this repo:
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
Create a virtual environment and install dependencies (example):

python -m venv venv
source venv/bin/activate    # macOS / Linux
# venv\Scripts\activate     # Windows PowerShell
pip install -r requirements.txt


If you don't have a requirements.txt, typical packages are:
streamlit, pydantic, and the LLM client you use (e.g., groq or other SDK).
