#!/usr/bin/env python3
"""
Builds and re-ranks todays_outreach_queue.csv with Best Fits First.
Uses multi-agent research findings and deep classification scoring.
"""

import csv
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILE = os.path.join(BASE_DIR, "todays_outreach_queue.csv")
SENT_LOG_FILE = os.path.join(BASE_DIR, "emails_sent.csv")
CANDIDATES_FILE = os.path.join(BASE_DIR, "candidates_summary.json")

# Load sent emails to strictly avoid duplicates
sent_emails = set()
if os.path.isfile(SENT_LOG_FILE):
    with open(SENT_LOG_FILE, "r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) > 4 and row[4] == "Success":
                sent_emails.add(row[1].lower().strip())

print(f"Total verified past sends: {len(sent_emails)}")

# Elite Researched AI Companies from Subagents (Tier 1: 90 - 100 Fit Score)
RESEARCHED_ELITE = [
    {
        "priority": "1 - Elite Fit (99)",
        "company": "SirionLabs",
        "contact_name": "Anurag Rana",
        "email": "anurag.rana@sirionlabs.com",
        "target_role": "AI Engineering Intern (Contract Intelligence & RAG)",
        "personalized_hook": "I've been closely following SirionLabs' category leadership in contract intelligence, which directly mirrors what I built with ContractIQ—a RAG assistant providing verbatim source quote attribution and automated adversarial prompt injection evaluations."
    },
    {
        "priority": "1 - Elite Fit (98)",
        "company": "Suki",
        "contact_name": "Ashwin Singh",
        "email": "ashwin.singh@suki.ai",
        "target_role": "AI Engineering Intern (Voice & Clinical AI)",
        "personalized_hook": "I've been tracking Suki's ambient clinical voice AI and EHR integrations, which strongly connects to my project ClinicVoice AI—a multi-agent voice receptionist for clinics built with LangGraph, Groq, Bedrock, and red-team safety guardrails."
    },
    {
        "priority": "1 - Elite Fit (98)",
        "company": "Roboflow",
        "contact_name": "Roboflow Labs Team",
        "email": "labs@roboflow.com",
        "target_role": "Applied Multimodal AI / Computer Vision Research Intern",
        "personalized_hook": "Having built FieldProof AI—a multimodal video QA platform leveraging Google Gemini and asynchronous PostgreSQL job queues to audit technician job execution—I am eager to contribute to Roboflow Labs' work operationalizing frontier VLMs and real-time vision pipelines."
    },
    {
        "priority": "1 - Elite Fit (98)",
        "company": "Secomind.AI",
        "contact_name": "Sanika Arora",
        "email": "sanika@piri.ai",
        "target_role": "AI Engineering Intern (Multi-Agent & Platform Workflows)",
        "personalized_hook": "With hands-on experience building LangGraph-driven multi-agent systems in ClinicVoice AI and production API connectors during my DCS AI internship, I'm eager to engineer autonomous multi-agent workers and tool integrations for StudioX."
    },
    {
        "priority": "1 - Elite Fit (97)",
        "company": "Shipsy",
        "contact_name": "Arun Kumar",
        "email": "arun.kumar@shipsy.io",
        "target_role": "AI Agentic Systems / AI Engineering Intern",
        "personalized_hook": "Having built ClinicVoice AI—an autonomous multi-agent voice receptionist on LangGraph and Bedrock—and ContractIQ for automated contract auditing, I can immediately contribute to scaling Shipsy's AgentFleet (Clara & Nexa) and AgentFlow orchestration."
    },
    {
        "priority": "1 - Elite Fit (97)",
        "company": "Observe.AI",
        "contact_name": "Terence Anthony",
        "email": "terence@observe.ai",
        "target_role": "AI Engineering Intern (Voice & Agentic Systems)",
        "personalized_hook": "I've been following Observe.AI's conversation intelligence and agentic contact center platforms, which directly aligns with my experience building multi-agent voice workflows and CI/CD evaluation harnesses in ClinicVoice AI."
    },
    {
        "priority": "1 - Elite Fit (96)",
        "company": "Prodigal",
        "contact_name": "Sonam Mohapatra",
        "email": "sonam.mohapatra@prodigaltech.com",
        "target_role": "Conversational AI / Speech Intelligence Engineering Intern",
        "personalized_hook": "Having engineered ClinicVoice AI—a multi-agent voice receptionist orchestrating low-latency LLMs via LangGraph and Model Context Protocol with an automated red-team safety evaluation harness—I can immediately contribute to scaling Prodigal's proAgent voice workflows and automated compliance auditing engines."
    },
    {
        "priority": "1 - Elite Fit (96)",
        "company": "Detect Technologies",
        "contact_name": "Gripson Martes",
        "email": "gripson@detecttechnologies.com",
        "target_role": "AI Engineering Intern (Computer Vision & Video QA)",
        "personalized_hook": "I've been following Detect Technologies' automated video intelligence, which directly relates to my project FieldProof AI where I used Gemini to audit technician job videos with human-in-the-loop review and background job queues."
    },
    {
        "priority": "1 - Elite Fit (95)",
        "company": "Pixis",
        "contact_name": "Vaibhav R",
        "email": "vaibhav.r@pixis.ai",
        "target_role": "Agentic AI / GenAI Platform Intern",
        "personalized_hook": "Given Pixis's multi-agent architecture and Model Context Protocol (MCP) integration over Amazon Bedrock, my experience architecting ClinicVoice AI with LangGraph and MCP—alongside building enterprise RAG systems with Groq—maps directly to Pixis's living memory and autonomous agent ecosystem."
    },
    {
        "priority": "1 - Elite Fit (95)",
        "company": "Wobot.ai",
        "contact_name": "Hiring Team",
        "email": "hr@wobot.ai",
        "target_role": "AI Engineering Intern (Video Analytics & Multimodal)",
        "personalized_hook": "I've been following Wobot.ai's video intelligence platform for automated SOP compliance, which strongly parallels FieldProof AI—a multi-tenant platform I built using Gemini to audit field work videos against structured checklists."
    },
    {
        "priority": "1 - Elite Fit (95)",
        "company": "BUDDI AI",
        "contact_name": "Shailender Nr",
        "email": "shailender.nr@buddi.ai",
        "target_role": "AI Engineering Intern (Healthcare NLP & RAG)",
        "personalized_hook": "I've been tracking BUDDI AI's clinical automation and medical NLP platform, which resonates with my experience building ClinicVoice AI with medical safety layers and winning 1st Prize at the AGRHINOVA Hackathon."
    },
    {
        "priority": "1 - Elite Fit (95)",
        "company": "Leena AI",
        "contact_name": "Sanya Nagpal",
        "email": "sanya@leena.ai",
        "target_role": "AI Engineering Intern (Enterprise Agents & RAG)",
        "personalized_hook": "I've been following Leena AI's autonomous enterprise agents, which directly matches my experience building multi-agent systems in LangGraph and my Linkific internship deploying enterprise RAG on PostgreSQL with pgvector."
    },
    {
        "priority": "1 - Elite Fit (95)",
        "company": "InfraCloud Technologies",
        "contact_name": "Rahul Inamdar",
        "email": "rahul.inamdar@infracloud.io",
        "target_role": "AI Infrastructure & Cloud Engineering Intern",
        "personalized_hook": "I've been following InfraCloud's contributions to cloud-native MLOps and Kubernetes architectures, which resonates with my hands-on background deploying containerized multi-agent systems and automated CI/CD testing pipelines."
    },
    {
        "priority": "1 - Elite Fit (94)",
        "company": "Recro",
        "contact_name": "Alok Singh",
        "email": "alok.singh@recro.io",
        "target_role": "Generative AI / Agentic Systems Intern",
        "personalized_hook": "My work engineering LangGraph multi-agent architectures with rigorous eval harnesses in ClinicVoice AI and deploying enterprise RBAC RAG at Linkific directly aligns with Recro's focus on production-grade agentic workflows and AI Pods."
    },
    {
        "priority": "1 - Elite Fit (94)",
        "company": "Claim Genius",
        "contact_name": "Amit Prayagi",
        "email": "amit.prayagi@claimgenius.com",
        "target_role": "Multimodal Computer Vision Intern",
        "personalized_hook": "My work building FieldProof AI—an automated video audit platform processing multimodal technician streams using Gemini with human-in-the-loop review—and my multimodal pipeline work at DCS AI align directly with Claim Genius's vision models for automated vehicle damage inspection."
    },
    {
        "priority": "1 - Elite Fit (93)",
        "company": "Supervity",
        "contact_name": "Hiring Team",
        "email": "careers@supervity.ai",
        "target_role": "AI Agent & Workflow Engineering Intern",
        "personalized_hook": "With Supervity deploying autonomous AI Employees combining Agentic RAG, voice, and human-in-the-loop supervision, my hands-on background developing ClinicVoice AI's multi-agent routing and FieldProof AI's asynchronous human-review pipelines offers immediate synergy."
    },
    {
        "priority": "1 - Elite Fit (93)",
        "company": "Haptik",
        "contact_name": "Nimesh Mathur",
        "email": "nimesh@haptik.ai",
        "target_role": "Applied AI / Conversational AI Intern",
        "personalized_hook": "I've been following Haptik's conversational GenAI agents, which aligns with my work designing multi-agent dialogue flows in LangGraph and integrating secure LLM backends with role-based access control."
    },
    {
        "priority": "1 - Elite Fit (93)",
        "company": "Trilogy Innovations",
        "contact_name": "Anuja",
        "email": "anuja@codenation.co.in",
        "target_role": "Software Engineering Intern (AI & Core Systems)",
        "personalized_hook": "I've been following Trilogy Innovations' culture of elite systems engineering, which aligns with my focus on building resilient end-to-end backends, strict automated CI/CD testing, and algorithmic problem-solving."
    },
    {
        "priority": "1 - Elite Fit (92)",
        "company": "Ressl AI",
        "contact_name": "Arushi Gandhi",
        "email": "arushi@ressl.ai",
        "target_role": "Autonomous Agent / Applied AI Intern (YC W26)",
        "personalized_hook": "Given Ressl AI's focus on autonomous workflow agents automating complex enterprise CRM operations, my experience architecting multi-agent tool execution via Model Context Protocol (MCP) in ClinicVoice AI and enterprise connectors at DCS AI translates directly to your Salesforce agent runtime."
    },
    {
        "priority": "1 - Elite Fit (92)",
        "company": "Reltio",
        "contact_name": "Anupam Srivastava",
        "email": "anupam.srivastava@reltio.com",
        "target_role": "AI / Data Platform Engineering Intern",
        "personalized_hook": "I've been tracking Reltio's AI-powered entity resolution and data unification platforms, which connects to my experience with vector embeddings, semantic search, and secure multi-tenant PostgreSQL architectures."
    },
    {
        "priority": "1 - Elite Fit (92)",
        "company": "CoreStack",
        "contact_name": "Anil K",
        "email": "anil.k@corestack.io",
        "target_role": "Cloud & AI Engineering Intern",
        "personalized_hook": "I've been following CoreStack's automated multi-cloud governance and compliance engines, which aligns with my work designing anomaly detection models (SentinelAI) and automated API test suites."
    },
    {
        "priority": "1 - Elite Fit (91)",
        "company": "Element5",
        "contact_name": "Giridhar D",
        "email": "giridhar.d@e5.ai",
        "target_role": "AI Engineering Intern (Healthcare Workflows)",
        "personalized_hook": "I've been following Element5's post-acute healthcare automation, which connects with my background building ClinicVoice AI's multi-agent appointment engine and my DCS AI internship integrating complex API workflows."
    },
    {
        "priority": "1 - Elite Fit (90)",
        "company": "SigNoz",
        "contact_name": "Hiring Team",
        "email": "hiring@signoz.io",
        "target_role": "AI Observability & Infrastructure Intern",
        "personalized_hook": "Having designed automated red-teaming, prompt injection evaluation harnesses, and strict citation tracking in ContractIQ and ClinicVoice AI, I am deeply excited to help build SigNoz's open-telemetry LLM tracing and agentic observability pipelines."
    },
    {
        "priority": "1 - Elite Fit (90)",
        "company": "Pelican.ai",
        "contact_name": "Rimpee Kukreja",
        "email": "rimpee.kukreja@pelican.ai",
        "target_role": "Machine Learning / Anomaly Detection Intern",
        "personalized_hook": "I've been tracking Pelican.ai's cognitive compliance solutions, which connects directly with my research project SentinelAI where I used Isolation Forests and Tree SHAP for adaptive anomaly and insider threat detection."
    },
    {
        "priority": "1 - Elite Fit (89)",
        "company": "Lumiq",
        "contact_name": "Dharmendra Rawat",
        "email": "dharmendra.rawat@lumiq.ai",
        "target_role": "AI / RAG Engineering Intern",
        "personalized_hook": "I've been tracking Lumiq's data and AI acceleration platforms for financial services, which connects directly with my project ContractIQ where I built RAG pipelines with verifiable verbatim citation extraction."
    },
    {
        "priority": "1 - Elite Fit (88)",
        "company": "CommerceIQ",
        "contact_name": "Jyoti Gouri",
        "email": "jyoti.gouri@commerceiq.ai",
        "target_role": "Applied AI / Multi-Agent Systems Intern",
        "personalized_hook": "As CommerceIQ scales its AllyAI multi-agent suite to orchestrate retail operations and content audits, my experience engineering LangGraph multi-agent collaboration in ClinicVoice AI and automated audit queues in FieldProof AI provides a direct foundation."
    },
    {
        "priority": "1 - Elite Fit (88)",
        "company": "Quartic.ai",
        "contact_name": "Priya Tyagi",
        "email": "priya@quartic.ai",
        "target_role": "Applied Machine Learning Intern",
        "personalized_hook": "I've been following Quartic.ai's industrial AI platform, which aligns with my background in machine learning model evaluation, automated CI/CD testing pipelines, and anomaly detection."
    },
    {
        "priority": "1 - Elite Fit (88)",
        "company": "phData",
        "contact_name": "Manashi Chakraborty",
        "email": "manashi@phdata.io",
        "target_role": "Data & GenAI Engineering Intern",
        "personalized_hook": "I've been following phData's enterprise data and GenAI operationalization, which aligns with my background in relational and vector databases (PostgreSQL, pgvector, Redis) and production RAG implementations."
    },
    {
        "priority": "1 - Elite Fit (88)",
        "company": "DATAECONOMY",
        "contact_name": "Sailaja Saranu",
        "email": "sailaja@dataeconomy.io",
        "target_role": "Data AI & Generative AI Intern",
        "personalized_hook": "Because DATAECONOMY implements enterprise Bedrock architectures, RAG, and multi-agent workflows via xContext, my work deploying Bedrock multi-agent systems and pgvector-backed enterprise RAG is a direct technical match."
    },
    {
        "priority": "1 - Elite Fit (87)",
        "company": "Dimagi",
        "contact_name": "Hiring Team",
        "email": "careers@dimagi.com",
        "target_role": "GenAI Healthcare Solutions Intern",
        "personalized_hook": "My experience developing ClinicVoice AI—a resilient, safety-evaluated clinical voice receptionist integrating Bedrock, Groq, and calendar systems—closely mirrors Dimagi's mission to deploy safe, purpose-built conversational LLM agents for frontline healthcare."
    },
    {
        "priority": "1 - Elite Fit (86)",
        "company": "bluCognition",
        "contact_name": "Rohit Singh",
        "email": "rohit.singh@blucognition.ai",
        "target_role": "Machine Learning / Data Science Intern",
        "personalized_hook": "I've been tracking bluCognition's advanced risk intelligence models, which strongly connects to my research project SentinelAI using Isolation Forests and Tree SHAP for explainable anomaly detection."
    },
    {
        "priority": "1 - Elite Fit (86)",
        "company": "Lentra",
        "contact_name": "Madhushree Kumra",
        "email": "madhushree.kumra@lentra.ai",
        "target_role": "Applied GenAI / Machine Learning Intern",
        "personalized_hook": "With Lentra transforming lending through Lentra Wingman's document-auditing GenAI and conversational journeys, my work engineering ContractIQ's verbatim quote citation RAG and SentinelAI's anomaly detection algorithms offers immediate value."
    },
    {
        "priority": "1 - Elite Fit (86)",
        "company": "impress.ai",
        "contact_name": "Soumya Somanathan",
        "email": "soumya@impress.ai",
        "target_role": "AI Engineering Intern (Dialogue & NLP)",
        "personalized_hook": "I've been following impress.ai's conversational assessment platform, which connects to my experience developing multi-agent conversational systems with LangGraph and semantic search validation pipelines."
    },
    {
        "priority": "1 - Elite Fit (85)",
        "company": "Blackstraw.ai",
        "contact_name": "Radhika Boppana",
        "email": "radhika.boppana@blackstraw.ai",
        "target_role": "Enterprise GenAI & MLOps Intern",
        "personalized_hook": "As Blackstraw builds enterprise-grade agentic platforms, multimodal video processing, and RAG architectures with strict MLOps guardrails, my hands-on portfolio spanning FieldProof AI and Linkific makes me well-prepared to build across your stack."
    },
    {
        "priority": "1 - Elite Fit (85)",
        "company": "PandoCorp",
        "contact_name": "Honeydeep Sabharwal",
        "email": "honeydeep@pando.ai",
        "target_role": "Enterprise AI / Agentic Systems Intern",
        "personalized_hook": "Having engineered ContractIQ to automate document review with verbatim verification and built enterprise AI connector integrations at DCS AI, I can help advance Pando's 'Pi' autonomous logistics agents."
    },
    {
        "priority": "1 - Elite Fit (85)",
        "company": "Neewee",
        "contact_name": "Mahesh Bandaru",
        "email": "mahesh@neewee.ai",
        "target_role": "Industrial AI & Systems Intern",
        "personalized_hook": "I've been following Neewee's Bodhee platform for manufacturing predictive intelligence, which connects with my background in machine learning model evaluation and automated diagnostic platforms."
    },
    {
        "priority": "1 - Elite Fit (85)",
        "company": "Enterprise Minds",
        "contact_name": "Phani Kalyan",
        "email": "phani@eminds.ai",
        "target_role": "Agentic AI & Solutions Engineering Intern",
        "personalized_hook": "With hands-on experience building LangGraph multi-agent workflows with tool-calling via MCP and enterprise connectors at DCS AI, I can help Enterprise Minds develop robust agentic automations for complex enterprise environments."
    },
    {
        "priority": "1 - Elite Fit (84)",
        "company": "KritiKal Solutions",
        "contact_name": "Priyom Barooah",
        "email": "priyom.barooah@kritikalvision.ai",
        "target_role": "Computer Vision & Multimodal AI Intern",
        "personalized_hook": "Given KritiKal Solutions' 20+ years delivering cutting-edge computer vision inspection and video analytics, my experience developing FieldProof AI—a multimodal video QA system auditing compliance via Gemini—aligns closely with your vision solutions."
    },
    {
        "priority": "1 - Elite Fit (83)",
        "company": "Ternuvo AI",
        "contact_name": "Hiring Team",
        "email": "careers@ternuvoai.com",
        "target_role": "Full-Stack AI Engineering Intern",
        "personalized_hook": "My background building end-to-end production GenAI applications—including pgvector RAG at Linkific, prompt injection defenses in ContractIQ, and LangGraph multi-agent systems—aligns seamlessly with Ternuvo AI's client-facing AI delivery model."
    },
    {
        "priority": "1 - Elite Fit (81)",
        "company": "LearnTube.ai",
        "contact_name": "Gargi",
        "email": "gargi@learntube.ai",
        "target_role": "Multimodal GenAI Intern",
        "personalized_hook": "My experience building FieldProof AI to ingest and analyze multimodal video streams using Gemini, combined with multimodal video/audio workflows at DCS AI Technologies, directly connects with LearnTube's mission to convert video content into structured learning."
    },
    {
        "priority": "1 - Elite Fit (78)",
        "company": "Zendrive",
        "contact_name": "Hiring Team",
        "email": "careers@zendrive.com",
        "target_role": "Machine Learning / Telematics Intern",
        "personalized_hook": "My experience building SentinelAI—employing unsupervised anomaly detection algorithms like Isolation Forest and One-Class SVM with Tree SHAP explainability—provides strong mathematical and modeling alignment with Zendrive's sensor-based driver risk models."
    },
    {
        "priority": "1 - Elite Fit (76)",
        "company": "Easy Eat AI",
        "contact_name": "Rakshita Shharma",
        "email": "rakshita@easyeat.ai",
        "target_role": "AI Engineering Intern (Recommendations & Backend)",
        "personalized_hook": "With EasyEat leveraging AI to power smart dining recommendations and end-to-end restaurant automation, my experience developing low-latency agentic workflows and asynchronous job processing in ClinicVoice AI and FieldProof AI translates well to high-volume F&B ordering."
    },
    {
        "priority": "1 - Elite Fit (76)",
        "company": "Moonfrog Labs",
        "contact_name": "Harshita Rathore",
        "email": "harshita@moonfroglabs.com",
        "target_role": "Backend & AI / Data Science Intern",
        "personalized_hook": "Having built SentinelAI for behavioral anomaly detection and architected high-throughput job queue pipelines in FieldProof AI, I can contribute directly to Moonfrog's real-time backend reliability and player anti-fraud telemetry models."
    },
    {
        "priority": "1 - Elite Fit (74)",
        "company": "West Agile Labs",
        "contact_name": "Hari Prashanth",
        "email": "hari.prashanth@westagilelabs.com",
        "target_role": "Full-Stack AI Engineering Intern",
        "personalized_hook": "Leveraging my experience building end-to-end full-stack AI applications—from PostgreSQL-backed multimodal platforms in FieldProof AI to enterprise RAG systems at Linkific—I can help West Agile Labs deliver production-grade AI features for client products."
    },
    {
        "priority": "1 - Elite Fit (72)",
        "company": "SynfraCore",
        "contact_name": "Hiring Team",
        "email": "careers@synfracore.com",
        "target_role": "AI Curriculum & Engineering Intern",
        "personalized_hook": "With my background delivering enterprise RAG architectures and multi-agent AI systems, I can help expand SynfraCore's advanced AI Engineering academy tracks and enhance the SynfraAI technical tutoring assistant."
    }
]

# Track emails already slotted in Tier 1
slotted_emails = set()
final_queue = []

for item in RESEARCHED_ELITE:
    em = item["email"].lower().strip()
    if em not in sent_emails and em not in slotted_emails:
        final_queue.append({
            "Priority": item["priority"],
            "Company": item["company"],
            "Contact_Name": item["contact_name"],
            "Email": em,
            "Target_Role": item["target_role"],
            "Personalized_Hook": item["personalized_hook"]
        })
        slotted_emails.add(em)

print(f"Added {len(final_queue)} Researched Elite companies to Top of Queue!")

# Now load candidates from master excel or json
candidates = []
if os.path.isfile('recruiter_master_leads.xlsx'):
    import pandas as pd
    df_m = pd.read_excel('recruiter_master_leads.xlsx')
    # Row 1 is header: SNo, Name, Email, Title, Company
    for _, row in df_m.iloc[2:].iterrows():
        em = str(row.iloc[2]).strip().lower() if len(row) > 2 else ''
        if '@' in em and '.' in em.split('@')[1]:
            name = str(row.iloc[1]).strip() if len(row) > 1 else 'Hiring Team'
            title = str(row.iloc[3]).strip() if len(row) > 3 else 'HR'
            comp = str(row.iloc[4]).strip() if len(row) > 4 else 'your company'
            candidates.append({
                'email': em,
                'name': name,
                'title': title,
                'company': comp,
                'domain': em.split('@')[1]
            })
    print(f'Loaded {len(candidates)} candidates from recruiter_master_leads.xlsx')


# Classification Heuristics
bpo_staffing_patterns = [
    'bpo', 'staffing', 'manpower', 'recruitment', 'placement', 'consulting',
    'consultancy', 'infotech', 'services pvt', 'solutions pvt', 'associates',
    'technologies pvt ltd', 'call center', 'transcription', 'data entry',
    'back office', 'telecom services', 'human resources pvt'
]

scored_remaining = []
for c in candidates:
    em = c.get("email", "").strip().lower()
    if em in sent_emails or em in slotted_emails or not em:
        continue

    comp = c.get("company", "").strip()
    comp_lower = comp.lower()
    dom = c.get("domain", "").lower()
    title = c.get("title", "").lower()
    name = c.get("name", "").strip() or "Hiring Team"

    score = 50

    # Domain bonus
    if any(d in dom for d in ['.ai', 'ai.', '-ai', 'ml.', 'data.', 'analytics.', 'vision.', 'labs.']):
        score += 30
    elif any(d in dom for d in ['.io', '.tech', '.dev', 'cloud', 'software']):
        score += 15

    # Company name bonus
    if re.search(r'\b(ai|ml|intelligence|robotics|neural|vision|voice)\b', comp_lower):
        score += 25
    elif re.search(r'\b(analytics|data|cloud|cyber|security|platform|software|labs)\b', comp_lower):
        score += 15

    # Title bonus
    if any(t in title for t in ['talent', 'head', 'lead', 'director', 'technical recruiter', 'vp']):
        score += 8

    # Penalties
    for neg in bpo_staffing_patterns:
        if neg in comp_lower or neg in dom:
            score -= 35
            break

    c_score = min(max(score, 5), 90)

    # Determine Tier Label & Hook
    if c_score >= 70:
        priority_label = f"2 - Tech / SaaS ({c_score})"
        role = "AI / Software Engineering Intern"
        hook = f"I've been following how {comp} is driving innovation in software and data engineering, which connects to my experience building end-to-end AI backends and RAG systems."
    elif c_score >= 50:
        priority_label = f"3 - General Software ({c_score})"
        role = "Software Engineering Intern"
        hook = f"I've been following what {comp} is building in modern technology and software engineering."
    else:
        priority_label = f"4 - Generic IT / Support ({c_score})"
        role = "Software Engineering Intern"
        hook = f"I've been following {comp}'s technology services and engineering initiatives."

    scored_remaining.append({
        "score": c_score,
        "Priority": priority_label,
        "Company": comp,
        "Contact_Name": name,
        "Email": em,
        "Target_Role": role,
        "Personalized_Hook": hook
    })
    slotted_emails.add(em)

# Sort remaining by score descending
scored_remaining.sort(key=lambda x: x["score"], reverse=True)

for item in scored_remaining:
    final_queue.append({
        "Priority": item["Priority"],
        "Company": item["Company"],
        "Contact_Name": item["Contact_Name"],
        "Email": item["Email"],
        "Target_Role": item["Target_Role"],
        "Personalized_Hook": item["Personalized_Hook"]
    })

# Write out the new prioritized queue
fieldnames = ["Priority", "Company", "Contact_Name", "Email", "Target_Role", "Personalized_Hook"]
with open(QUEUE_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(final_queue)

print("=" * 60)
print(f"✅ Successfully rebuilt {QUEUE_FILE} with BEST FITS FIRST!")
print(f"Total Leads in Prioritized Queue: {len(final_queue)}")
print("=" * 60)
print("Top 15 Leads in Queue (Will be emailed first):")
for i, lead in enumerate(final_queue[:15], 1):
    print(f"  {i}. [{lead['Priority']}] {lead['Company']} ({lead['Email']}) -> {lead['Target_Role']}")
print("=" * 60)
