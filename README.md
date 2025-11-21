# 🚀 Advocai — Autonomous Health Insurance Appeal System

**Kaggle Agents Intensive — Capstone Project (Agents for Good)**
A production-aligned multi-agent system that converts denied health insurance claims into fully structured, clinically supported, and legally compliant appeal packages.

---

# 📘 Overview

Health insurance denials often rely on opaque internal guidelines and automated algorithms. Patients rarely possess the clinical or legal expertise required to navigate appeals effectively.

**Advocai changes this.**
It ingests denial letters, extracts structured data, retrieves medical evidence, analyzes regulatory frameworks, drafts a legally defensible appeal, and validates it through an internal QA agent.

This transforms a traditionally complex, time-intensive process into a fully automated, transparent workflow.

---

# ✨ Key Features

* **Four-Agent Intelligence Pipeline**
  Auditor → Clinician → Regulatory → Barrister → Judge

* **Robust PDF/OCR ingestion** for denial & policy documents

* **Clinical evidence retrieval** (PubMed tool + internal knowledge base)

* **Regulatory reasoning engine** based on statutes & coverage mandates

* **Legal-grade appeal generation**

* **Automated quality evaluation** via Judge Agent

* **Persistent workflow state** (JSON/SQLite)

* **Deployment-ready architecture** with modular tools

---

# 🧠 Multi-Agent Architecture

```
User PDF
   │
   ▼
Auditor Agent (Extracts structure)
   │
   ▼
Clinician Agent (Retrieves medical evidence)
   │
   ▼
Regulatory Agent (Legal + compliance analysis)
   │
   ▼
Barrister Agent (Drafts legal appeal)
   │
   ▼
Judge Agent (Evaluates & validates output)
   │
   ▼
Final Appeal Package (PDF + Evidence + JSON)
```

---

# 🔍 Agent Responsibilities

## 🕵️ Auditor Agent — *Extraction Layer*

* OCR + text block parsing
* Denial code detection
* Policy clause extraction
* Produces **Structured Denial Object**

## 🩺 Clinician Agent — *Medical Intelligence*

* Searches PubMed / internal policy-linked evidence base
* Identifies guideline support + clinical justification
* Produces **Clinical Evidence Report**

## ⚖️ Regulatory Agent — *Compliance & Statute Layer*

Ensures the appeal adheres to legal frameworks.

### Key Capabilities:

* Retrieves:

  * State-mandated coverage rules
  * Federal protections (ERISA, ACA)
  * Prior appeal precedents
* Analyzes:

  * Policy vs law conflicts
  * Mandated coverage overrides
* Outputs:
  **Legal Leverage Point**
  e.g., “State Mandate §45A requires coverage for X under medically necessary conditions.”

## 🏛️ Barrister Agent — *Legal Drafting*

* Synthesizes all agent outputs
* Drafts a professional, structured, citation-backed appeal letter
* Creates a submission-ready PDF package

## 👨‍⚖️ Judge Agent — *Quality Assurance*

* Evaluates factual accuracy
* Checks evidence alignment
* Ensures legal tone & logical consistency
* Flags hallucinations
* Produces a **scorecard + recommended status**

---

# 🧱 Phase II Enhancements (Production Alignment)

Phase II transforms Advocai from a working MVP into a resilient, extensible, competition-grade architecture.

## ✓ A. Expanded Agent Ecosystem

* Addition of **Regulatory Agent**
* Addition of **Judge Agent**
  This elevates the system from 3 to **5 cooperating agents**, each with a domain-specialized role.

## ✓ B. Durable State & Session Management

To handle long workflows and recover gracefully:

### Session Directory Structure:

```
sessions/
  <session_id>/
     auditor_output.json
     clinician_output.json
     regulatory_output.json
     barrister_output.json
     judge_report.json
```

This enables:

* Fault tolerance
* Resumability
* Debuggability
* Asynchronous agent execution

Supports both:

* **JSON-based storage** (simple & transparent)
* **SQLite-based storage** (ACID compliant)

## ✓ C. Toolchain Hardening

* Cleaner PDF ingestion
* Efficient PubMed search wrapper
* Law library builder for regulatory reasoning

---

# 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Viraj281105/Advocai.git
cd Advocai
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```ini
GEMINI_API_KEY=your_key
PUBMED_API_KEY=optional_key
TESSERACT_CMD=/usr/bin/tesseract
OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

---

# ▶️ Running Advocai

### Basic Execution

```bash
python main.py \
  --input path/to/denial.pdf \
  --policy path/to/policy.pdf \
  --out ./output
```

The output will include:

* Appeal letter
* Evidence bundle
* Extracted structured data
* Judge agent evaluation

---

# 🗂️ Project Structure (Final)

```
Advocai/
├─ advocai/
│  ├─ agents/
│  │  ├─ auditor.py
│  │  ├─ clinician.py
│  │  ├─ regulatory.py
│  │  ├─ barrister.py
│  │  └─ data/
│  │     ├─ input/
│  │     └─ knowledge/
│  ├─ __init__.py
│
├─ tools/
│  ├─ document_reader.py
│  ├─ pubmed_search.py
│  ├─ build_law_library.py
│  └─ __init__.py
│
├─ output/
│  ├─ appeal_case_1_CO-50.txt
│  └─ truth/
│     └─ case_1.json
│
├─ docs/
│  ├─ Architecture Diagram.png
│  ├─ Capstone Project Details.docx
│  ├─ Phase 1 MVP Documentation.docx
│  └─ Phase 2 USP Documentation.docx
│
├─ app.py
├─ main.py
├─ requirements.txt
├─ LICENSE
└─ README.md
```

---

# 🧪 Testing

### Unit Tests

```bash
pytest tests/unit
```

### End-to-End Pipeline Tests

```bash
pytest tests/e2e
```

---

# 🔐 Security & Compliance

* No sensitive PHI stored in logs
* Local OCR and processing recommended
* Statutory logic hosted in offline knowledge base
* Appeal output includes required disclaimers

---

# 📈 Limitations & Future Work

* OCR accuracy depends on scan quality
* PubMed limits may affect evidence depth
* Regulatory knowledge base expansion underway
* Web dashboard (Streamlit) planned as UI layer
* API layer in future release

---

# 👥 Team

| Role                  | Member     | Kaggle Username |
| --------------------- | ---------- | --------------- |
| Lead Developer        | Viraj Jadhao | virajjadhao281105 |
| Documentation & Pitch | Bhumi Sirvi | bhumisirvi27 |
| Clinical Agent Dev    | Harsh Jain | patterncracker |
| Tools & Deployment    | Yash Doke | user_4          |

---

# 📄 License

MIT License