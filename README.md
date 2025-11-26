# 🚀 **AdvocAI — Autonomous Health Insurance Appeal System**

### *Production-Ready Multi-Agent Framework for Medical, Regulatory, and Legal Reasoning*

**Kaggle: 5-Day Agents Intensive — Capstone Project (Agents for Good)**
**Author:** Viraj Jadhao & Team
**Architecture:** Multi-Agent | Hybrid LLM | PubMed Tooling | OCR | Regulatory Law Engine | Persistent Workflow

---

# 🏛️ Executive Summary

Insurance claim denials are a widespread challenge across healthcare. Patients lack:

* medical research expertise
* policy interpretation expertise
* legal argumentation expertise
* the time or literacy to decode insurer language

Appeal letters often fail not because patients shouldn’t win — but because they can’t articulate their case with **clinical, statutory, and legal force.**

**AdvocAI solves this.**

It is a **fully automated, end-to-end multi-agent system** that transforms a denied claim into:

* A **structured denial representation**
* A **clinically validated evidence report**
* A **legally compliant regulatory brief**
* A **fully drafted appellate letter**
* A **judge-validated scorecard**
* A **complete appeal package** (PDF + JSON + evidence bundle)

This is done through **5 cooperating LLM agents**, supported by PubMed, OCR, database-backed checkpoints, and an orchestrator that guarantees fault-tolerant execution.

AdvocAI is engineered to be **production-aligned**, **modular**, **extensible**, and **resumable**.

---

# 🧠 **High-Level Multi-Agent Architecture**

```
            ┌─────────────────────────┐
            │   Denial Letter (PDF)   │
            └─────────────┬───────────┘
                          │ OCR + Parsing
                          ▼
         ┌────────────────────────────────────┐
         │         Auditor Agent              │
         └─────────────┬──────────────────────┘
                       │ Structured Denial Object
                       ▼
         ┌────────────────────────────────────┐
         │         Clinician Agent            │
         └─────────────┬──────────────────────┘
                       │ PubMed + Medical Evidence
                       ▼
         ┌────────────────────────────────────┐
         │        Regulatory Agent            │
         └─────────────┬──────────────────────┘
                       │ Statutory Legal Points
                       ▼
         ┌────────────────────────────────────┐
         │        Barrister Agent             │
         └─────────────┬──────────────────────┘
                       │ Appeal Letter Draft
                       ▼
         ┌────────────────────────────────────┐
         │          Judge Agent               │
         └─────────────┬──────────────────────┘
                       │ Scorecard + Validation
                       ▼
               Final Appeal Package
```

Each agent is isolated with its own prompt engineering, error handling, and LLM execution pipeline.

---

# 🧬 **Five-Agent Pipeline: Deep Technical Overview**

Below is a full breakdown of each agent, its responsibilities, tools, inputs, outputs, and technical design principles.

---

## 🕵️ **1. Auditor Agent — Extraction & Structuring Layer**

### **Purpose**

Transforms denial & policy PDFs into a structured, machine-readable object.

### **Capabilities**

* OCR + text block extraction (Tesseract or PyMuPDF)
* Snippet-based clause detection
* Denial code parsing
* Policy language extraction
* Deduplication & relevance scoring

### **Input**

* `denial.pdf`
* `policy.pdf`

### **Output (Pydantic Model: StructuredDenial)**

```json
{
  "procedure_denied": "Genomic Sequencing for Early Cancer Detection",
  "denial_code": "CO-50",
  "insurer_reason_snippet": "...",
  "policy_clause_text": "..."
}
```

---

## 🩺 **2. Clinician Agent — Medical Evidence & PubMed Research**

### **Purpose**

Produce scientifically grounded justification supporting procedure necessity.

### **PubMed Integration**

* Uses custom tool: `tools/pubmed_search.py`
* Query generation via LLM
* Articles parsed into:

  * Title
  * Summary of findings
  * PMID
  * Evidence strength

### **Output (EvidenceList)**

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

### **Fallback Logic**

If PubMed returns nothing → synthesizes *zero-article evidence list* and still proceeds.

---

## ⚖️ **3. Regulatory Agent — Legal & Compliance Engine**

### **Purpose**

Extract applicable legal precedents and statutory mandates.

### **Powered by**

* **Gemini** primary
* **Ollama Llama3.2** fallback (automatic)
* **Knowledge Base** in `advocai/data/knowledge/policies/` + `statutes.md`

### **Output**

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

### **Hybrid Fallback Sequence**

```
Gemini → Gemini (retry) → Ollama → SystemError stub
```

This ensures the system **NEVER blocks** the pipeline.

---

## 🏛️ **4. Barrister Agent — Legal Draft Assembly**

### **Purpose**

Draft the final appeal using:

* structured denial details
* clinical evidence
* regulatory points

### **Output**

A polished, multi-section appeal letter (4,000–6,000 chars typical).

### **Technical Features**

* Unified Gemini text extractor
* Automatic formatting blocks
* Non-blocking error handlers

---

## 👨‍⚖️ **5. Judge Agent — QA & Validation Layer**

### **Purpose**

Ensure appeal correctness, coherence, tone, and legal defensibility.

### **Checks**

* Hallucinations
* Evidence consistency
* Statutory correctness
* Tone alignment
* Structural completeness

### **Output**

Scorecard JSON:

```json
{
  "clinical_alignment": 0.91,
  "legal_compliance": 0.88,
  "structure_integrity": 1.0,
  "recommendation": "APPROVE"
}
```

---

# 🔥 **Hybrid LLM Strategy: Gemini + Ollama + AFC**

AdvocAI uses a **tiered inference system**:

### **Primary: Gemini 2.5 Flash**

Fast, high-quality reasoning layer.

### **Secondary: Ollama (Llama3.2)**

Local fallback:

* used automatically on rare Gemini failures
* ensures no stage breaks the pipeline

### **AFC (Auto Function Calling)**

Used by Clinician Agent for PubMed retrieval.

---

# 🏗️ **Orchestrator: Phase-II Production Engine**

### **Location:** `orchestrator/main.py`

This is the brain of AdvocAI.

## 🔑 Key Responsibilities

* Pipeline execution
* Parallelism & async scheduling
* Checkpointing each stage
* Postgres + JSON storage
* Hybrid LLM routing
* Automatic retries
* Resume-from-last-safestage

### 🧩 **safe_execute() Core Logic**

Pseudocode:

```
if checkpoint exists:
    load
else:
    run agent
    store outputs in Postgres + filesystem
```

### 💾 **Session Management**

Location: `storage/session_manager.py`

Stores:

* stage outputs
* timestamps
* raw LLM responses
* error traces

Backends:

* JSON
* PostgreSQL (connection pool)

---

# 🗂️ **Folder Structure (As in Your Screenshot)**

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
│   │   └── output/
│   │
│   └── tools/
│       ├── document_reader.py
│       ├── pubmed_search.py
│       ├── build_law_library.py
│       └── io_utils.py
│
├── orchestrator/
│   ├── app.py          # FastAPI server
│   ├── cli.py          # CLI runner
│   └── main.py         # Pipeline orchestrator
│
├── sessions/
│   └── .gitkeep
│
├── storage/
│   └── session_manager.py
│
├── docs/
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 🛠️ Installation

```bash
git clone https://github.com/Viraj281105/Advocai.git
cd Advocai
python -m venv advocai_env
advocai_env\Scripts\activate   # Windows
pip install -r requirements.txt
```

Add `.env`:

```
GEMINI_API_KEY=xxxx
POSTGRES_URL=xxxx
```

---

# ▶️ Running AdvocAI

## **1️⃣ Using the API (FastAPI)**

### Start server:

```bash
uvicorn orchestrator.app:app --reload
```

### Upload denial + policy PDFs:

```
POST /start
```

### Check status:

```
GET /status/{session_id}
```

### Fetch results:

```
GET /result/{session_id}
```

---

## **2️⃣ Using the CLI**

```bash
python orchestrator/cli.py \
    --denial data/input/denial_case_1.pdf \
    --policy data/input/policy_case_1.pdf \
    --case case_1
```

Outputs will appear in:

```
data/output/<case_id>/
```

---

# 🧪 Testing

### Unit Tests

```
pytest tests/unit
```

### End-to-End

```
pytest tests/e2e
```

---

# 🔐 Security & PHI Handling

* Do not log raw PHI
* Use local OCR instead of cloud OCR
* Regulatory datasets remain offline
* Session data stored locally unless required otherwise

---

# 📊 Benchmarks (Internal)

| Component          | Avg Time |
| ------------------ | -------- |
| Auditor            | 2.1s     |
| Clinician (PubMed) | 6–10s    |
| Regulatory         | 3s       |
| Barrister          | 2–4s     |
| Judge              | 1–2s     |

---

# 🧭 Future Roadmap

* Streamlit web dashboard
* Additional medical tools (UpToDate API)
* Full ERISA/ACA statute embedding search
* Model switching interface (Gemini Pro, GPT-4.1, Claude 3.5)
* PDF Appeal Packet auto-generator
* Multi-user tenancy
* Cost tracking and rate-limit forecasting

---

# 🏁 Final Notes

AdvocAI is now architected as a:

✔ **Fault-tolerant**
✔ **Resume-capable**
✔ **Hybrid-LLM**
✔ **Production-aligned**
✔ **Multi-agent**
✔ **API + CLI compatible**

system that demonstrates real-world AI agent engineering.