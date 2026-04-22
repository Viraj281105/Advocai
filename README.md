# 🚀 AdvocAI — Autonomous Health Insurance Appeal System

### *A Production-Ready Multi-Agent Framework for Medical, Regulatory & Legal Reasoning*

[![Python](https://img.shields.io/badge/Python-77.1%25-blue)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)](https://nextjs.org/)
[![PLpgSQL](https://img.shields.io/badge/PLpgSQL-2.7%25-336791)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Viraj281105/Advocai/blob/main/LICENSE)
[![Contributors](https://img.shields.io/badge/Contributors-2-green)](https://github.com/Viraj281105/Advocai/graphs/contributors)
![GitHub stars](https://img.shields.io/github/stars/Viraj281105/Advocai?style=social)

**Authors:** Viraj Jadhao & Bhumi Sirvi  
**Architecture:** Multi-Agent | Hybrid LLM | PubMed Tooling | OCR | Legal Rule Engine | Persistent Workflow

---

<p align="center">
  <img src="docs/ThumbNail.png" width="560" height="280">
</p>

---

## 🏛️ Executive Summary

Every year, millions of valid medical insurance claims are denied due to poor documentation literacy, lack of access to clinical evidence, misinterpretation of policy clauses, and inability to construct legally defensible arguments.

**67% of denied claims are never appealed**, despite **45% of appealed claims being overturned.**

This gap exists not because patients don't deserve approval — but because they cannot navigate the required **medical, legal, and administrative complexity**.

**AdvocAI fixes this.**

It is a **fully autonomous, end-to-end multi-agent system** that turns a denied claim into:

- A structured denial representation
- A PubMed-backed medical evidence dossier
- A statutory & regulatory compliance brief
- A polished appellate letter
- A judge-validated QA scorecard
- A complete appeal package (PDF + JSON + evidence bundle)

Engineered to be **modular**, **fault-tolerant**, **hybrid-LLM**, and **production-aligned**.

---

## 🧠 System Architecture

<p align="center">
  <img src="docs/Architecture Diagram 2.png" width="900">
</p>

```
Denial PDF + Policy PDF
        ↓
   Auditor Agent          (OCR, parsing, ICD/CPT extraction)
        ↓
  Clinician Agent         (PubMed evidence retrieval & synthesis)
        ↓
  Regulatory Agent        (ACA / ERISA statute matching)
        ↓
  Barrister Agent         (appellate letter drafting)
        ↓
    Judge Agent           (QA scoring & validation)
        ↓
  Appeal Package Output   (PDF + JSON + evidence bundle)
```

---

## 🧬 Pipeline — 5 Core Agents

### 🕵️ 1. Auditor Agent — OCR, Parsing & Structuring

Converts denial and policy PDFs into a structured machine-readable object via OCR preprocessing, text block segmentation, ICD/CPT code extraction, policy-clause detection, and relevance ranking.

```json
{
  "procedure_denied": "Genomic Sequencing",
  "denial_code": "CO-50",
  "insurer_reason_snippet": "...",
  "policy_clause_text": "..."
}
```

---

### 🩺 2. Clinician Agent — PubMed Evidence Engine

Generates medically grounded justification for treatment necessity using a PubMed API wrapper, LLM query generation, and evidence extraction with PMI/DOI verification.

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

### ⚖️ 3. Regulatory Agent — Law & Statute Reasoner

Identifies relevant coverage mandates (ACA, ERISA, state statutes) via legal rule matching and policy-language conflict detection. Runs fully locally via **Mistral on Ollama** with a stub fallback for edge cases.

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

### 🏛️ 4. Barrister Agent — Appellate Draft Generator

Composes a structured, professional appeal letter with legal-tone control, evidence and policy integration, section structuring, and consistency preservation.

---

### 👨‍⚖️ 5. Judge Agent — QA, Validation & Scoring

Evaluates completeness, coherence, factuality, and legal defensibility. Checks citation accuracy, legal compliance, clinical alignment, structure integrity, and hallucination detection.

```json
{
  "clinical_alignment": 0.91,
  "legal_compliance": 0.88,
  "structure_integrity": 1.0,
  "recommendation": "APPROVE"
}
```

---

## 🔥 LLM Architecture — Fully Local

AdvocAI runs entirely on-device via [Ollama](https://ollama.com/), with no external API dependencies. All inference and embedding is GPU-accelerated on local hardware.

| Role | Model |
|------|-------|
| **Inference** | Mistral (via Ollama) — primary reasoning and generation |
| **Embeddings** | Mistral Sentence Transformers — local semantic search & retrieval |
| **Orchestration** | Ollama client — unified local model serving |
| **Tool Use** | PubMed API + local retrieval pipeline |

**Development Hardware:**

| Component | Spec |
|-----------|------|
| CPU | Intel Core Ultra 9 275 HX |
| GPU | NVIDIA RTX 5070 (GPU-accelerated inference) |
| RAM | 32 GB |
| Storage | 1 TB SSD |
| Machine | ASUS ROG Strix G16 G615LP |

All models run locally — **zero cloud inference, zero API costs, full data privacy.**

---

## 🏗️ Pipeline Orchestrator

**Location:** `orchestrator/main.py`

The orchestrator handles pipeline control flow, retry and fallback logic, stage checkpointing, session tracking, resume-from-last-stage, and local Ollama model routing.

```python
if checkpoint exists:
    load previous output
else:
    run agent
    save checkpoint
```

**Storage backends:** JSON filesystem (default) · PostgreSQL (optional)

---

## 📁 Repository Structure

```
Advocai/
│
├── advocai/                        # Core package
│   ├── agents/                     # Agent implementations
│   │   ├── auditor/
│   │   ├── clinician/
│   │   ├── regulatory/
│   │   ├── barrister/
│   │   └── judge/
│   ├── config/                     # Package-level configuration
│   ├── data/
│   │   ├── input/
│   │   ├── knowledge/
│   │   │   └── policies/
│   │   └── output/
│   └── tools/
│       ├── document_reader.py
│       ├── pubmed_search.py
│       ├── build_law_library.py
│       └── io_utils.py
│
├── frontend/                       # Next.js web frontend
│   ├── src/
│   └── public/
│
├── models/
│   └── local-embedder/             # Local embedding model
│       ├── 1_Pooling/
│       └── 2_Normalize/
│
├── orchestrator/                   # Pipeline orchestration engine
│   ├── main.py
│   ├── cli.py                      # CLI interface
│   ├── app.py                      # FastAPI server
│   └── auth/
│
├── storage/
│   ├── json/                       # JSON checkpoint filesystem
│   └── postgres/
│       └── migrations/             # PLpgSQL database migrations
│
├── sessions/                       # Per-session state persistence
│
├── tools/                          # Shared tool utilities
├── config/                         # Top-level configuration
│
├── requirements.txt
├── LICENSE                         # MIT License
├── .gitignore
└── README.md
```

---

## 🛠️ Installation

```bash
git clone https://github.com/Viraj281105/Advocai.git
cd Advocai

python -m venv advocai_env

# Windows:
advocai_env\Scripts\activate
# macOS/Linux:
source advocai_env/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_key_here
POSTGRES_URL=optional
```

> ⚠️ Never commit your `.env` file — it is already listed in `.gitignore`.

---

## ▶️ Running AdvocAI

### Production Mode (All-in-one)

```bash
# Build the frontend first
cd frontend
npm run build
cd ..

# Start Ollama, Backend, and Frontend
.\start_prod.bat
```

### Development Mode

```bash
.\start_dev.bat
```

### API Mode

```bash
uvicorn orchestrator.app:app --reload
```

### CLI Mode

```bash
python orchestrator/cli.py \
    --denial data/input/denial.pdf \
    --policy data/input/policy.pdf \
    --case case_1
```

### Frontend (Next.js Development)

```bash
cd frontend
npm install
npm run dev
```

---

## 📊 Performance Benchmarks

| Agent | Avg Latency |
|-------|-------------|
| Auditor | 2.1s |
| Clinician | 6–10s |
| Regulatory | 3s |
| Barrister | 2–4s |
| Judge | 1–2s |
| **End-to-end** | **~15–22s** |

---

## 🔐 Security

- No PHI leakage to logs
- Offline OCR processing
- Offline legal corpora
- Encrypted session data

---

## 🧭 Roadmap

- [x] Next.js web dashboard
- [ ] ERISA/ACA statute embeddings
- [ ] Advanced PubMed summarizer
- [ ] Multi-jurisdiction legal packs
- [x] Auto PDF appeal packet compiler
- [x] Full multi-user system

---

## ⚖️ License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👥 Authors

**Viraj Jadhao** — Real-time systems + AI engineering  
📂 [github.com/Viraj281105](https://github.com/Viraj281105)

**Bhumi Sirvi** — AI engineering + Backend systems  

---

*AdvocAI isn't a demo. It's a production-aligned multi-agent system capable of navigating the complex intersection of medicine, law, and policy to produce high-quality, appeal-ready insurance documents.*
