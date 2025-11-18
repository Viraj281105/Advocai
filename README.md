# 🚀 Advocai: The Autonomous Health Insurance Advocate

> **Kaggle Agents Intensive - Capstone Project | Track: Agents for Good**



---

## 🎯 Project Pitch: Fighting Denial with Data (30 Points)

This section directly addresses the core **Pitch** criteria: Problem, Solution, and Value.

### 1. The Problem: The Insurance Denial Trap
Health insurance companies often use proprietary algorithms to issue systematic claim denials, leaving patients with massive, unexpected bills. The manual appeal process is complex, stressful, and requires specialized legal and medical knowledge that the average patient lacks, resulting in a low success rate. This problem creates financial hardship and emotional distress for vulnerable populations.

### 2. The Solution: Advocai’s Autonomous Swarm
**Advocai** is a sequential **Multi-Agent System** designed to dismantle claim denials by autonomously assembling a clinically and legally sound appeal package. It transforms unstructured denial letters (PDFs) into structured, actionable evidence for appeal.

### 3. Key Value and Impact
* **Democratization of Advocacy:** Provides every patient with expert legal and clinical support, effectively leveling the playing field against large insurers.
* **Time & Stress Reduction:** Reduces the patient’s active involvement from weeks of manual research and drafting to a simple document upload.
* **Tangible Financial Impact:** Successfully reversing a single denied claim can save a user thousands of dollars, demonstrating high real-world value.

---

## 🛠️ Technical Architecture & Implementation (70 Points)

Advocai utilizes a team of specialist agents working in sequence to achieve the final outcome.

### The Agent Swarm
1.  **The Auditor Agent:** Ingests the raw denial letter (PDF) and policy data, extracting the precise **Denial Code** and the specific **Policy Clause**.
2.  **The Clinician Agent:** Searches external medical databases using the Denial Code to find authoritative clinical evidence proving the treatment was "medically necessary."
3.  **The Barrister Agent:** Takes all gathered evidence and drafts a formal, legally structured appeal letter, ready for submission.

### Required Concepts Implemented (Must check 3+)
- [x] **Multi-agent System:** Three distinct, sequentially cooperating agents (Auditor, Clinician, Barrister).
- [x] **Tools:** Use of a custom **PubMed API** tool and a **PDF/OCR Tool** for document analysis.
- [x] **Sessions & Memory:** The Auditor’s structured findings are stored in `InMemorySessionService` and explicitly passed as context to the subsequent agents.
- [ ] Context Engineering
- [ ] Agent Evaluation

---

## ⚙️ Setup & Installation

1.  **Prerequisites:** Python 3.9+ and Git.
2.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/Viraj281105/Advocai.git](https://github.com/Viraj281105/Advocai.git)
    cd Advocai
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Ensure your `requirements.txt` file is populated with necessary packages like `google-genai`, `pydantic`, `pypdf`, etc.)*

4.  **Set up Environment Variables:**
    * Create a file named `.env` in the root directory.
    * Add your API keys:
      ```
      # Must use Gemini for Bonus Points
      GEMINI_API_KEY=your_key_here 
      # OPTIONAL: Other API keys for specialized tools
      PUBMED_API_KEY=optional_key_here
      ```

5.  **Run Advocai:**
    ```bash
    python main.py
    ```

---

## ⭐ Bonus Points & Team Roster

### Team Advocai
| Role | Name | Kaggle Username |
| :--- | :--- | :--- |
| Lead Developer | [Your Name] | [Your Username] |
| Documentation & Pitch | [Teammate 2] | [Username 2] |
| Clinical Agent Dev | [Teammate 3] | [Username 3] |
| Tools & Deployment | [Teammate 4] | [Username 4] |

### Bonus Criteria
- [ ] **Effective Use of Gemini:** (5 Points)
- [ ] **Agent Deployment Evidence:** (5 Points - Provide documentation for Cloud Run/Vertex AI)
- [ ] **YouTube Video Submission:** (10 Points)
  * [Link to YouTube Video URL]