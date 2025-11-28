![badge-labs](https://user-images.githubusercontent.com/327285/230928932-7c75f8ed-e57b-41db-9fb7-a292a13a1e58.svg)

# DTCC AI Hackathon 2025: Empowering India's Innovators
The purpose of hackathon is to leverage AI and ML Technologies to address critical challenges in the financial markets. The overall goal is to progress industry through Innovation, Networking and by providing effective Solutions.

**Hackathon Key Dates** 
•	June 6th - Event invites will be sent to participants
•	June 9th - Hackathon Open
•	June 9th-11th - Team collaboration and Use Case development
•	June 12th - Team presentations & demos
•	June 16th - Winners Announcement

More Info - https://communications.dtcc.com/dtcc-ai-hackathon-registration-17810.html

Commit Early & Commit Often!!!

## Project Name: AURA Regulatory Graph Comparison & KOP Generation Platform

### Project Details
A web-based application that enables regulatory analysts and operations teams to upload, compare, and approve regulatory documents. It extracts entity relationships using LLM (Gemini/Vertex AI), constructs directed graphs, detects differences between regulatory versions, and generates Key Operating Procedures (KOP) in Word format.

---

## 🔍 Features

- **PDF Upload (First-time & Comparison Mode)**: Upload new or updated regulation PDFs.
- **LLM Integration**: Uses Vertex AI/Gemini for contextual summarization and entity relationship extraction.
- **Graph Visualization**: Interactive graph rendering using Vis.js to depict regulatory relationships.
- **Graph Comparison**: Highlights added/changed edges between old and new regulations.
- **KOP Generation**: One-click generation of Word-based KOP documents from regulatory summaries and graphs.
- **Audit Trail**: Stores all uploads, summaries, graphs, and history for compliance and traceability.
- **Responsive UI**: Clean and user-friendly HTML interface for regulatory analysis workflows.

---

## 📁 Project Structure

```
project-root/
│
├── app.py                     # Main Flask application
├── db_models.py              # SQLAlchemy ORM models for PostgreSQL
├── utils.py                  # PDF text extraction, graph parsing & comparison
├── anthropic_llm.py             # LLM invocation for summarization and relationship extraction
│
├── templates/
│   ├── index.html            # Upload page
│   ├── compare.html          # Graph comparison and KOP generation screen
│   └── history.html          # History log of uploads
│
├── static/                   # JS, CSS, and assets
├── requirements.txt          # Python dependencies
└── README.md                 # You're here!
```

---

## 🧪 Tech Stack

- **Backend**: Python 3.x, Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **LLM**: Anthropic Cluade Sonet 4
- **Graph Engine**: NetworkX
- **Frontend**: HTML5, JavaScript (Vis.js, html2canvas)
- **Document Generation**: `python-docx`

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/regulation-graph-kop.git
cd regulation-graph-kop
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Database

Update `app.py` with your PostgreSQL credentials:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://<username>:<password>@<host>:<port>/<dbname>'
```

Initialize DB tables:

```bash
python
>>> from app import db, app
>>> with app.app_context():
...     db.create_all()
...
```

### 4. Configure Anthropic AI

Set your GCP environment variable:

```bash
export BEDROCK_MODEL_ARN=<inference_profile_arn>
```

### 5. Run the Application

```bash
python app.py
```

Visit [http://localhost:5000](http://localhost:5000) in your browser.

---

## 🧠 How It Works

1. **Upload PDFs**: Choose regulation and upload new or both old/new PDFs.
2. **LLM Analysis**: Summarizes content, extracts entities & relationships.
3. **Graph Rendering**: Builds interactive directed graphs with tooltips.
4. **Comparison Logic**: Highlights modified or newly added edges.
5. **KOP Generation**: Uses LLM to generate operational steps as a Word doc.

---

## 📦 Dependencies

- Flask
- SQLAlchemy
- psycopg2-binary
- python-docx
- fitz (PyMuPDF)
- networkx
- anthropic
- boto3
- html2canvas (JS)

Install them using:

```bash
pip install -r requirements.txt
```

### Team Information


## Using DCO to sign your commits

**All commits** must be signed with a DCO signature to avoid being flagged by the DCO Bot. This means that your commit log message must contain a line that looks like the following one, with your actual name and email address:

```
Signed-off-by: John Doe <john.doe@example.com>
```

Adding the `-s` flag to your `git commit` will add that line automatically. You can also add it manually as part of your commit log message or add it afterwards with `git commit --amend -s`.

See [CONTRIBUTING.md](./.github/CONTRIBUTING.md) for more information

### Helpful DCO Resources
- [Git Tools - Signing Your Work](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)
- [Signing commits
](https://docs.github.com/en/github/authenticating-to-github/signing-commits)


## License

Copyright 2025 FINOS

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)








