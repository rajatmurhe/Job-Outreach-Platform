# Specialized Resumes Directory

Place your role-tailored resume PDFs into this directory or the project root. The engine automatically matches the target job role from the leads queue and attaches the corresponding PDF.

### Suggested File Naming Conventions

| Filename | Role Category | Example Target Roles |
| :--- | :--- | :--- |
| `resume_agentic_ai.pdf` | **Agentic AI & GenAI Systems** | AI Agentic Systems, GenAI Platform Intern, LangGraph Engineer |
| `resume_voice_conversational.pdf` | **Voice & Conversational AI** | Conversational AI Intern, Speech Intelligence, Clinical Voice AI |
| `resume_computer_vision.pdf` | **Computer Vision & Video AI** | Computer Vision Intern, Multimodal Video QA, Deep Learning |
| `resume_rag_nlp.pdf` | **RAG, Document AI & NLP** | RAG Engineer, Document Intelligence, LegalTech AI, NLP Intern |
| `resume_ml_systems.pdf` | **Machine Learning & Systems** | ML Intern, Anomaly Detection, AI Infrastructure, Observability |
| `resume_general_swe.pdf` | **Core Software & AI Engineering** | Software Engineering Intern, Full-Stack AI, Backend Engineer |

### Customizing Match Keywords
You can customize the keyword-to-file mapping inside `get_resume_for_role(role)` in `daily_outreach_daemon.py` and `server.py`.
