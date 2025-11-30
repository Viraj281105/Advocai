# 🚀 **AdvocAI — Autonomous Health Insurance Appeal System**

### *A Production-Ready Multi-Agent Framework for Medical, Regulatory & Legal Reasoning*

**Kaggle: 5-Day Agents Intensive — Capstone Project (Agents for Good)**
**Author:** Viraj Jadhao & Team
**Architecture:** Multi-Agent | Hybrid LLM | PubMed Tooling | OCR | Legal Rule Engine | Persistent Workflow

---

# 🖼️ Project Thumbnail

<p align="center">
  <img src="docs/ThumbNail.png" width="560" height="280">
</p>

---

# 🏛️ **Executive Summary**

Every year, millions of valid medical insurance claims are denied due to:

* poor documentation literacy
* lack of access to clinical evidence
* misinterpretation of policy clauses
* inability to construct legally defensible arguments

**67% of denied claims are never appealed**, despite **45% of appealed claims being overturned.**

This gap exists not because patients don’t deserve approval—but because they cannot navigate the required **medical, legal, and administrative complexity**.

**AdvocAI fixes this.**

It is a **fully autonomous, end-to-end multi-agent system** that turns a denied claim into:

* A structured denial representation
* A PubMed-backed medical evidence dossier
* A statutory & regulatory compliance brief
* A polished appellate letter
* A judge-validated QA scorecard
* A complete appeal package (PDF + JSON + evidence bundle)

Engineered to be **modular**, **fault-tolerant**, **hybrid-LLM**, and **production-aligned**, AdvocAI demonstrates what real-world AI agents can achieve.

---

# 🧠 **System Architecture Overview**

<p align="center">
  <img src="docs/Architecture Diagram 2.png" width="900">
</p>

---

# 🧬 **Pipeline Overview — 5 Core Agents**

A full breakdown of each agent and its role in constructing a medically, legally, and procedurally airtight appeal.

---

## 🕵️ 1. **Auditor Agent — OCR, Parsing & Structuring**

### Purpose

Convert denial & policy PDFs into a structured machine-readable object.

### Responsibilities

* OCR preprocessing
* Text block segmentation
* ICD/CPT code extraction
* Policy-clause detection
* Relevance ranking

### Output Example

```json
{
  "procedure_denied": "Genomic Sequencing",
  "denial_code": "CO-50",
  "insurer_reason_snippet": "...",
  "policy_clause_text": "..."
}
```

---

## 🩺 2. **Clinician Agent — PubMed Evidence Engine**

### Purpose

Generate medically grounded justification supporting treatment necessity.

### Features

* PubMed API wrapper
* LLM query generation
* Evidence extraction + PMI/DOI verification

### Output

```json
{
  "root": [
    {
      "article_title": "...",
      "summary_of_finding": "...",
      "pubmed_id": "12345678"
    }
  ]
}
```

---

## ⚖️ 3. **Regulatory Agent — Law & Statute Reasoner**

### Purpose

Identify relevant coverage mandates (ACA, ERISA, state statutes).

### Features

* Legal rule matching
* Policy-language conflict detection
* Hybrid fallback (Gemini → Gemini Retry → Ollama → Stub)

### Output

```json
{
  "legal_points": [
    {
      "statute": "ACA §2713",
      "summary": "Requires insurers to cover ..."
    }
  ]
}
```

---

## 🏛️ 4. **Barrister Agent — Appellate Draft Generator**

### Purpose

Compose a structured, professional appeal letter.

### Features

* Legal-tone control
* Evidence + policy integration
* Section structuring
* Consistency preservation

---

## 👨‍⚖️ 5. **Judge Agent — QA, Validation & Scoring**

### Purpose

Evaluate completeness, coherence, factuality, and legal defensibility.

### Checks

* Citation accuracy
* Legal compliance
* Clinical alignment
* Structure integrity
* Hallucination detection

### Output

```json
{
  "clinical_alignment": 0.91,
  "legal_compliance": 0.88,
  "structure_integrity": 1.0,
  "recommendation": "APPROVE"
}
```

---

# 🔥 **Hybrid LLM Architecture**

### Primary

* **Gemini 2.5 Flash** — Fast, cost-efficient, high-quality reasoning.

### Secondary Fallback

* **Ollama Llama 3.2** — Offline, stable fallback engine.

### Tool Use

* **AFC (Auto Function Calling)** for PubMed evidence retrieval.

This ensures **zero pipeline breaks**, even under API outages.

---

# 🏗️ **Pipeline Orchestrator (Production Engine)**

Location: `orchestrator/main.py`

### Responsibilities

* Pipeline control flow
* Retry & fallback logic
* Stage checkpointing
* Session tracking
* Resume-from-last-stage
* Hybrid LLM routing

### Safe Execution Logic

```
if checkpoint exists:
    load previous output
else:
    run agent
    save checkpoint
```

### Storage Backends

* JSON filesystem
* PostgreSQL (optional)

---

# 📁 **Clean Project Tree (Final Version)**

```
Advocai/
│
├── advocai/
│   ├── agents/
│   │   ├── auditor.py
│   │   ├── clinician.py
│   │   ├── regulatory.py
│   │   ├── barrister.py
│   │   └── judge.py
│   │
│   ├── config/
│   ├── data/
│   │   ├── input/
│   │   ├── knowledge/
│   │   │   └── policies/
│   │   └── output/
│   │
│   └── tools/
│       ├── document_reader.py
│       ├── pubmed_search.py
│       ├── build_law_library.py
│       └── io_utils.py
│
├── orchestrator/
│   ├── main.py
│   ├── cli.py
│   └── app.py
│
├── storage/
│   ├── json/
│   └── postgres/
│       └── migrations/
│
├── sessions/
│
├── data/
│   ├── input/
│   ├── output/
│   └── truth/
│
├── docs/
│   ├── Architecture Diagram 2.png
│   └── ThumbNail.png
│
├── tools/
├── config/
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

# 🛠️ Installation

```bash
git clone https://github.com/Viraj281105/Advocai.git
cd Advocai
python -m venv advocai_env
advocai_env\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:

```
GEMINI_API_KEY=your_key_here
POSTGRES_URL=optional
```

---

# ▶️ Running AdvocAI

### **API Mode**

```bash
uvicorn orchestrator.app:app --reload
```

### **CLI Mode**

```bash
python orchestrator/cli.py \
    --denial data/input/denial.pdf \
    --policy data/input/policy.pdf \
    --case case_1
```

---

# 📊 Benchmarks

| Stage      | Avg Time |
| ---------- | -------- |
| Auditor    | 2.1s     |
| Clinician  | 6–10s    |
| Regulatory | 3s       |
| Barrister  | 2–4s     |
| Judge      | 1–2s     |

---

# 🔐 Security

* No PHI leakage to logs
* Offline OCR
* Offline legal corpora
* Encrypted session data

---

# 🧭 Roadmap

* Streamlit web dashboard
* ERISA/ACA statute embeddings
* Advanced PubMed summarizer
* Multi-jurisdiction legal packs
* Auto PDF appeal packet compiler
* Full multi-user system

---

# 🏁 Final Word

AdvocAI isn’t a demo.
It’s a **real, production-aligned multi-agent system** capable of navigating the complex intersection of medicine, law, and policy to produce **high-quality, appeal-ready** insurance documents.

This project demonstrates **true agent intelligence** and **real-world applicability**.