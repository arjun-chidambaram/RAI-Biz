import json
import os
import re
from typing import List, Dict, Any, Optional
from ..models import Business, AIApplication
from ..schemas import QuestionDefinition
from ..config import settings

# Map user input industry text to normalized canonical industry keys
INDUSTRY_NORMALIZATION_MAP = {
    "automotive": "automotive_services",
    "automotive services": "automotive_services",
    "car detailing": "automotive_services",
    "vehicle": "automotive_services",
    "recruitment": "recruitment_hr",
    "recruitment and hr": "recruitment_hr",
    "hr": "recruitment_hr",
    "human resources": "recruitment_hr",
    "talent": "recruitment_hr",
    "hiring": "recruitment_hr",
    "healthcare": "healthcare",
    "health": "healthcare",
    "medical": "healthcare",
    "clinical": "healthcare",
    "hospital": "healthcare",
    "banking": "banking_finance",
    "banking and finance": "banking_finance",
    "finance": "banking_finance",
    "fintech": "banking_finance",
    "credit": "banking_finance",
    "retail": "retail_ecommerce",
    "retail and e-commerce": "retail_ecommerce",
    "e-commerce": "retail_ecommerce",
    "ecommerce": "retail_ecommerce",
    "manufacturing": "manufacturing",
    "factory": "manufacturing",
    "industrial": "manufacturing",
    "education": "education",
    "edtech": "education",
    "school": "education",
    "transportation": "transportation_logistics",
    "transportation and logistics": "transportation_logistics",
    "logistics": "transportation_logistics",
    "technology": "technology_software",
    "technology and software": "technology_software",
    "software": "technology_software",
    "saas": "technology_software",
    "hospitality": "hospitality",
    "hotel": "hospitality",
    "restaurant": "hospitality",
    "tourism": "hospitality",
    "agriculture": "agriculture",
    "agtech": "agriculture",
    "farming": "agriculture"
}

def detect_industry_key(industry_raw: Optional[str], business_function: Optional[str] = None) -> str:
    """Classifies an industry string into a supported canonical industry key, prioritizing primary industry."""
    ind_str = (industry_raw or '').lower()
    for pattern, key in INDUSTRY_NORMALIZATION_MAP.items():
        if re.search(r'\b' + re.escape(pattern) + r'\b', ind_str):
            return key

    func_str = (business_function or '').lower()
    for pattern, key in INDUSTRY_NORMALIZATION_MAP.items():
        if re.search(r'\b' + re.escape(pattern) + r'\b', func_str):
            return key

    return "general_sme"

def get_supported_industries() -> List[Dict[str, str]]:
    return [
        {"id": "automotive_services", "label": "Automotive Services", "description": "Vehicle detailing, maintenance scheduling, and diagnostics AI"},
        {"id": "recruitment_hr", "label": "Recruitment & HR", "description": "Applicant resume parsing, candidate scoring, and hiring workflows"},
        {"id": "healthcare", "label": "Healthcare & Life Sciences", "description": "Clinical decision support, patient triage, and diagnostic assistance"},
        {"id": "banking_finance", "label": "Banking & Finance", "description": "Credit underwriting, fraud detection, and automated financial advisory"},
        {"id": "retail_ecommerce", "label": "Retail & E-commerce", "description": "Product recommendation, dynamic pricing, and inventory AI"},
        {"id": "manufacturing", "label": "Manufacturing & Robotics", "description": "Predictive maintenance, automated defect detection, and quality control"},
        {"id": "education", "label": "Education & EdTech", "description": "Automated evaluation, student performance analytics, and personalized tutoring"},
        {"id": "transportation_logistics", "label": "Transportation & Logistics", "description": "Route optimization, fleet dispatch, and automated logistics scheduling"},
        {"id": "technology_software", "label": "Technology & Software", "description": "Developer copilots, automated code review, and cybersecurity SaaS"},
        {"id": "hospitality", "label": "Hospitality & Tourism", "description": "Guest service assistants, dynamic booking, and concierge automation"},
        {"id": "agriculture", "label": "Agriculture & AgTech", "description": "Crop disease detection, yield prediction, and precision farming AI"},
        {"id": "general_sme", "label": "General SME Enterprise", "description": "Universal multi-dimensional Responsible AI governance framework"}
    ]

# ----------------- CURATED INDUSTRY QUESTION TEMPLATES -----------------
# Each template contains 5 questions per dimension (Fairness, Transparency, Privacy, Sustainability)
INDUSTRY_QUESTION_BANKS: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    # 1. AUTOMOTIVE SERVICES
    "automotive_services": {
        "fairness": [
            {
                "id": "F1",
                "question_text": "Does your organization conduct pre-deployment bias testing across customer demographic groups and vehicle categories for {app_name}?",
                "guidance": "Assess whether historical customer enquiry logs, vehicle service records, or booking databases were statistically tested for outcome disparities.",
                "why_it_matters": "Unchecked historical biases in training data translate directly into discriminatory service package recommendations, pricing quotes, or scheduling priority.",
                "evidence_required": "Pre-deployment parity audit reports, demographic disparity test logs, vehicle segment quote variance analysis.",
                "risk_category": "Algorithmic Disparity & Pricing Bias",
                "risk_severity": "Critical",
                "recommendation": "Perform Fairlearn demographic parity evaluations across customer zip codes and vehicle makes before deploying automated quote algorithms."
            },
            {
                "id": "F2",
                "question_text": "Are automated service recommendation rates and quote discounts continuously monitored for bias drift across vehicle tiers and customer segments?",
                "guidance": "Verify whether model suggestion acceptance and promotion allocations are benchmarked monthly to detect runtime fairness drift.",
                "why_it_matters": "Recommendation algorithms can drift over time, systematically disfavoring certain customer categories or over-charging specific vehicle owners.",
                "evidence_required": "Monthly service acceptance reports, discount distribution logs, cross-demographic quote charts.",
                "risk_category": "Runtime Bias Drift",
                "risk_severity": "High",
                "recommendation": "Establish continuous telemetry dashboards tracking service recommendation acceptance rates across customer demographics."
            },
            {
                "id": "F3",
                "question_text": "Do you maintain an established reporting and appeal channel for customers, vehicle owners, or shop staff to contest automated quotes or recommendations?",
                "guidance": "Check if an accessible customer contact method, appeal form, or manager review protocol exists for contested quotes or appointment allocations.",
                "why_it_matters": "Without an accessible dispute mechanism, erroneous package recommendations and customer dissatisfaction remain invisible until negative public reviews occur.",
                "evidence_required": "Published customer dispute procedure, customer service escalation guidelines, dispute resolution logs.",
                "risk_category": "Customer Redress Deficiency",
                "risk_severity": "High",
                "recommendation": "Publish an explicit customer dispute procedure on the website booking widget and inside service quote confirmation emails."
            },
            {
                "id": "F4",
                "question_text": "Are protected demographic proxies (e.g. customer postal code, neighborhood, luxury vehicle brand) documented in an AI governance model card?",
                "guidance": "Review whether your team maintains formal documentation detailing potential proxy variables and fairness trade-off rationales in pricing and service recommendations.",
                "why_it_matters": "Proxy variables like neighborhood or luxury vehicle make can quietly reintroduce socioeconomic discrimination into automated detailing pricing.",
                "evidence_required": "Completed Model Governance Card, proxy variable correlation matrix, pricing trade-off rationale.",
                "risk_category": "Proxy Variable Discrimination",
                "risk_severity": "Medium",
                "recommendation": "Document all features ingested by {app_name} and perform correlation tests between customer zip codes and vehicle valuation proxies."
            },
            {
                "id": "F5",
                "question_text": "Does your organization maintain a formal corrective action plan or retraining threshold when recommendation disparities exceed acceptable limits?",
                "guidance": "Determine if predefined disparity triggers mandate an operational pause, prompt re-weighting, or model retraining when recommendation rates diverge systematically.",
                "why_it_matters": "Identifying unfair recommendations is useless without a predetermined protocol to halt or remediate discriminatory automated workflows in customer recommendations.",
                "evidence_required": "Written corrective action plan, operational pause protocol, retraining trigger documentation.",
                "risk_category": "Lack of Remediation Protocol",
                "risk_severity": "High",
                "recommendation": "Draft an automated disparity threshold trigger that temporarily falls back to rule-based quotes if recommendation variance exceeds 20%."
            }
        ],
        "transparency": [
            {
                "id": "T1",
                "question_text": "Can {app_name} provide local and global explanations (e.g. SHAP values, feature importance) for why a specific service package was recommended?",
                "guidance": "Verify if service advisors and vehicle owners can inspect which input features (e.g., paint condition, vehicle age, usage frequency) influenced a specific service package recommendation.",
                "why_it_matters": "Black-box recommendations leave service advisors unable to justify suggested automotive treatments to customers or consumer protection auditors.",
                "evidence_required": "SHAP summary plots, individual customer explanation cards, service advisor explanation interface.",
                "risk_category": "Opaque Decisioning",
                "risk_severity": "High",
                "recommendation": "Deploy local SHAP feature attribution cards showing the top 3 vehicle conditions that triggered the detailing package recommendation."
            },
            {
                "id": "T2",
                "question_text": "Are affected customers explicitly notified when an AI or automated system has played a material role in service recommendations or scheduling?",
                "guidance": "Check if customers interacting with the online booking assistant or service kiosk receive clear disclosure that recommendations and appointment options are AI-generated.",
                "why_it_matters": "Emerging consumer protection and global regulations strictly mandate clear disclosure when consumers interact with automated AI agents.",
                "evidence_required": "Screenshot of chat/booking widget AI disclosure badge, terms of service automated decisioning clause.",
                "risk_category": "Consumer Disclosure Violation",
                "risk_severity": "High",
                "recommendation": "Add a clear visual disclosure badge stating 'AI-Powered Assistant' on the booking interface and quote summary notifications."
            },
            {
                "id": "T3",
                "question_text": "Are immutable audit logs maintained for every automated prediction, including vehicle inputs, recommended detailing packages, timestamp, and confidence score?",
                "guidance": "Inspect whether your database records historical customer inquiry inputs, vehicle details, recommended detailing packages, and pricing outputs for retrospective auditability.",
                "why_it_matters": "Without audit trails, defending against customer pricing disputes, service warranty claims, or recommendation errors is forensic guesswork.",
                "evidence_required": "Database audit log schema, query logs of historical recommendations, write-once storage policy.",
                "risk_category": "Audit Trail Absence",
                "risk_severity": "High",
                "recommendation": "Configure immutable JSON logging in the booking database capturing input features, recommended packages, and model version."
            },
            {
                "id": "T4",
                "question_text": "Is model performance (e.g. recommendation accuracy, concept drift) monitored periodically against actual technician inspection findings and customer reviews?",
                "guidance": "Assess whether recommendation accuracy and seasonal demand patterns are benchmarked monthly or quarterly against actual technician inspection findings and customer reviews.",
                "why_it_matters": "Data drift and seasonal shifts degrade model accuracy over time, leading to inappropriate service recommendations and lost customer revenue.",
                "evidence_required": "Quarterly accuracy benchmark reports, technician ground-truth validation logs, customer review correlation charts.",
                "risk_category": "Performance & Concept Drift",
                "risk_severity": "Medium",
                "recommendation": "Institute a monthly feedback loop comparing AI recommendations against service technician actual physical inspection findings."
            },
            {
                "id": "T5",
                "question_text": "Is a qualified service advisor or shop manager empowered to review, validate, or override high-impact automated recommendations before execution?",
                "guidance": "Confirm whether high-value detailing quotes (e.g. ceramic coating over $500), complex paint restoration packages, or booking cancellations require service advisor review.",
                "why_it_matters": "Human oversight acts as the critical failsafe against automated hallucinations, incorrect pricing, and gross customer dissatisfaction.",
                "evidence_required": "Service advisor sign-off workflow, override logs, staff training documentation on AI override procedures.",
                "risk_category": "Unchecked Automation Risk",
                "risk_severity": "Critical",
                "recommendation": "Require mandatory service advisor approval in the shop CRM before any automated detailing quote above $500 is confirmed."
            }
        ],
        "privacy": [
            {
                "id": "P1",
                "question_text": "Does your data ingestion pipeline enforce data minimization by screening and stripping unnecessary customer PII and vehicle identifiers before model processing?",
                "guidance": "Evaluate whether customer phone numbers, driver's licenses, vehicle registration/VIN details, and payment information are masked or discarded prior to inference.",
                "why_it_matters": "Storing and processing extraneous customer PII drastically magnifies GDPR, CCPA, and data breach liability in the event of an automotive shop data leak.",
                "evidence_required": "Regex masking script in pipeline, data schema with masked fields, PII redaction test logs.",
                "risk_category": "PII Exposure & Non-Minimization",
                "risk_severity": "Critical",
                "recommendation": "Implement an automated PII sanitizer in the input gateway masking customer phone numbers and payment card numbers before AI processing."
            },
            {
                "id": "P2",
                "question_text": "Is access to AI training datasets, model weights, and inference logs restricted via granular Role-Based Access Controls (RBAC) and MFA?",
                "guidance": "Review permissions to verify that only authorized personnel can access sensitive customer contact details, vehicle service histories, or appointment logs.",
                "why_it_matters": "Permissive internal access and shared shop tablet logins are leading root causes of customer data leaks and insider threats.",
                "evidence_required": "RBAC policy matrix, user directory MFA enrollment audit, shop terminal access log.",
                "risk_category": "Access Control Vulnerability",
                "risk_severity": "High",
                "recommendation": "Enforce individual authenticated user accounts with MFA for CRM access and eliminate shared shop floor tablet logins."
            },
            {
                "id": "P3",
                "question_text": "Is there a defined, automated data retention and disposal schedule for customer chat transcripts, vehicle photos, and booking logs?",
                "guidance": "Determine whether temporary customer chat inquiries, vehicle assessment photos, and legacy booking records are securely purged or anonymized after a defined period (e.g. 12 months).",
                "why_it_matters": "Indefinite data hoarding violates privacy regulations and magnifies forensic exposure during cybersecurity incidents.",
                "evidence_required": "Written data retention policy, automated TTL deletion script, secure disposal audit logs.",
                "risk_category": "Unlawful Data Retention",
                "risk_severity": "High",
                "recommendation": "Deploy a 12-month automated TTL purge on raw customer enquiry audio, chat transcripts, and temporary vehicle inspection photos."
            },
            {
                "id": "P4",
                "question_text": "Are all sensitive customer and vehicle data fields encrypted both in transit (TLS 1.3) and at rest (AES-256) throughout the entire AI pipeline?",
                "guidance": "Verify cryptographic protection on database volumes, customer communications, cloud storage buckets, and intermediate caching layers.",
                "why_it_matters": "Unencrypted customer booking batches and cache files expose the organization to immediate regulatory fines upon breach.",
                "evidence_required": "TLS certificate configuration, database encryption at rest verification, cloud storage bucket encryption policy.",
                "risk_category": "Cryptographic Non-Compliance",
                "risk_severity": "Critical",
                "recommendation": "Enforce TLS 1.3 across all customer-facing endpoints and enable AES-256 database volume encryption on booking storage."
            },
            {
                "id": "P5",
                "question_text": "Does the organization maintain documented data governance procedures, privacy impact assessments (PIA), and vendor vetting for AI tools?",
                "guidance": "Assess whether third-party conversational AI APIs, cloud hosts, and messaging sub-processors undergo written data protection and confidentiality reviews.",
                "why_it_matters": "SMEs are legally accountable for third-party sub-processors; using unvetted AI APIs can leak proprietary and customer data.",
                "evidence_required": "Executed third-party Data Processing Agreements (DPA), completed vendor PIA, AI tool risk evaluation.",
                "risk_category": "Third-Party Vendor Exposure",
                "risk_severity": "Medium",
                "recommendation": "Execute standard data processing addendums with external LLM API vendors guaranteeing zero customer data retention for model retraining."
            }
        ],
        "sustainability": [
            {
                "id": "S1",
                "question_text": "Does your team track compute duration, GPU/CPU utilization, and estimated energy consumption for model training and batch inference runs?",
                "guidance": "Check if runtime telemetry or cloud billing compute-hour metrics are monitored for hosting the detailing assistant and recommendation endpoints.",
                "why_it_matters": "You cannot reduce carbon impact or optimize runaway cloud compute costs without measuring baseline energy consumption.",
                "evidence_required": "Cloud Monitoring compute-hour dashboard, power draw estimation spreadsheet, monthly ESG telemetry logs.",
                "risk_category": "Unmonitored Compute Emissions",
                "risk_severity": "Medium",
                "recommendation": "Set up automated CloudWatch / Cloud Monitoring alerts tracking compute-hours and estimated monthly carbon footprint."
            },
            {
                "id": "S2",
                "question_text": "Are AI computing resources optimized (e.g. right-sizing cloud instances, auto-scaling to zero when idle, leveraging spot instances)?",
                "guidance": "Verify if customer inquiry servers scale down during non-business hours or dynamically match online appointment booking traffic.",
                "why_it_matters": "Idle GPU/cloud instances outside shop operating hours generate unnecessary carbon emissions and drain SME operating capital.",
                "evidence_required": "Auto-scaling policy configuration, scheduled shutdown script, instance sizing review.",
                "risk_category": "Resource Inefficiency",
                "risk_severity": "Medium",
                "recommendation": "Configure container auto-scaling to scale down inference workers to minimum capacity between 10 PM and 6 AM shop local time."
            },
            {
                "id": "S3",
                "question_text": "Does the system avoid unnecessary redundant processing by caching inference results and executing batched evaluations where applicable?",
                "guidance": "Confirm whether repetitive identical queries (e.g., standard detailing package recommendations for common car models) hit a low-latency cache rather than re-running deep model inference.",
                "why_it_matters": "Redundant re-computation wastes electric power and multiplies API token/inference expenses.",
                "evidence_required": "Redis / in-memory cache configuration, cache hit ratio statistics, batching pipeline code.",
                "risk_category": "Redundant Computation",
                "risk_severity": "Low",
                "recommendation": "Implement an in-memory cache for standard car detailing package recommendations for the top 50 vehicle makes and models."
            },
            {
                "id": "S4",
                "question_text": "Have your engineers evaluated lightweight, energy-efficient model architectures (e.g. distilled models, quantization, classical ML) before choosing heavy foundation models?",
                "guidance": "Assess whether compact models (e.g. LightGBM, quantized small models) were benchmarked against massive multi-billion parameter networks for routine package matching and slot scheduling.",
                "why_it_matters": "Using massive LLMs or oversized transformers for routine booking or classification tasks consumes 100x more energy for negligible accuracy gain.",
                "evidence_required": "Model benchmarking trade-off report, INT8 quantization benchmarks, model selection rationale document.",
                "risk_category": "Architectural Bloat",
                "risk_severity": "Medium",
                "recommendation": "Replace oversized LLM prompt passes for appointment scheduling with lightweight rule-based or distilled classification models."
            },
            {
                "id": "S5",
                "question_text": "Does the organization evaluate the regional carbon intensity and renewable energy factor of the cloud data centers hosting its AI workloads?",
                "guidance": "Determine if cloud workloads are hosted in data centers with low carbon grid factors (e.g., regions powered by hydro/solar/nuclear).",
                "why_it_matters": "Hosting customer-facing AI workloads in a clean grid region can cut actual operational greenhouse gas emissions by up to 70%.",
                "evidence_required": "Cloud hosting region audit, data center PUE / carbon coefficient record, region migration plan.",
                "risk_category": "High-Carbon Grid Deployment",
                "risk_severity": "Low",
                "recommendation": "Migrate persistent AI inference workloads to a cloud region with >80% renewable grid composition (e.g., us-central1, europe-west1)."
            }
        ]
    },

    # 2. RECRUITMENT AND HR
    "recruitment_hr": {
        "fairness": [
            {
                "id": "F1",
                "question_text": "Does your organization conduct pre-deployment bias and parity testing across demographic groups (e.g. gender, age, ethnicity) for {app_name}?",
                "guidance": "Assess whether applicant resume datasets or candidate ratings have been statistically evaluated for 4/5ths rule compliance and representation disparities.",
                "why_it_matters": "Unchecked historical biases in training data translate directly into discriminatory automated hiring, screening, or candidate ranking decisions.",
                "evidence_required": "Fairlearn disparate impact analysis, candidate selection distribution reports, 4/5ths rule statistical audit.",
                "risk_category": "Algorithmic Disparity & EEOC Exposure",
                "risk_severity": "Critical",
                "recommendation": "Execute formal demographic parity checks on candidate selection rates and adjust decision thresholds to meet EEOC standards."
            },
            {
                "id": "F2",
                "question_text": "Are group outcome metrics (e.g. demographic parity ratio, false rejection rates) continuously evaluated during operational hiring cycles?",
                "guidance": "Evaluate whether candidate selection rates across demographic groups are monitored on a recurring schedule to catch runtime bias drift.",
                "why_it_matters": "Models that appear fair in offline tests frequently experience disparate rejection rates when deployed against changing applicant applicant pools.",
                "evidence_required": "Quarterly applicant demographic monitoring reports, selection rate disparity tracking logs.",
                "risk_category": "Hiring Bias Drift",
                "risk_severity": "High",
                "recommendation": "Schedule quarterly audits comparing candidate pass-through rates across gender and ethnic groups for each open job category."
            },
            {
                "id": "F3",
                "question_text": "Do you have an established reporting mechanism for applicants, employees, or recruiters to report suspected algorithmic bias or unfair rejection?",
                "guidance": "Check if a clear contact method, appeal form, or independent dispute channel exists for rejected candidates.",
                "why_it_matters": "Without an accessible feedback or dispute mechanism, discriminatory screening decisions remain hidden until litigation or public exposure occurs.",
                "evidence_required": "Candidate appeal policy document, candidate inquiry mailbox logs, dispute resolution workflow.",
                "risk_category": "Applicant Recourse Absence",
                "risk_severity": "High",
                "recommendation": "Provide an accessible candidate feedback link in all automated rejection notices enabling human review requests."
            },
            {
                "id": "F4",
                "question_text": "Are candidate proxy features (e.g. university prestige, graduation year, postal code) documented and audited in an AI governance model card?",
                "guidance": "Review whether your team maintains formal documentation detailing potential proxy variables and fairness trade-off rationales in candidate ranking.",
                "why_it_matters": "Proxy variables can quietly reintroduce protected demographic traits into automated resume parsing models.",
                "evidence_required": "Model Governance Card, proxy variable correlation analysis, feature exclusion log.",
                "risk_category": "Proxy Feature Infiltration",
                "risk_severity": "Medium",
                "recommendation": "Drop or neutralize high-correlation proxy variables such as college graduation year (age proxy) and home address (racial proxy)."
            },
            {
                "id": "F5",
                "question_text": "Does your organization maintain a documented corrective action plan or retraining threshold when candidate selection disparity exceeds legal limits?",
                "guidance": "Determine if predefined disparity triggers mandate an operational hiring pause, re-weighting, or model retraining.",
                "why_it_matters": "Identifying hiring bias is useless without a predetermined protocol to halt or remediate discriminatory automated workflows.",
                "evidence_required": "Written corrective action plan, operational suspension protocol, model retraining criteria.",
                "risk_category": "Absence of Corrective Protocol",
                "risk_severity": "High",
                "recommendation": "Establish an automated alert that pauses automated resume ranking if candidate selection ratio falls below 0.80 for any demographic group."
            }
        ],
        "transparency": [
            {
                "id": "T1",
                "question_text": "Can {app_name} provide local and global explanations (e.g. SHAP values) showing why a specific candidate was shortlisted or rejected?",
                "guidance": "Verify if recruiters and candidates can inspect which resume attributes (e.g. experience, specific skills) positively or negatively influenced the decision.",
                "why_it_matters": "Black-box hiring tools leave organizations unable to justify employment decisions to candidates or civil rights regulatory bodies.",
                "evidence_required": "SHAP feature attribution visualizer, candidate score breakdown reports, recruiter explanation UI.",
                "risk_category": "Opaque Candidate Screening",
                "risk_severity": "High",
                "recommendation": "Generate an automated decision summary card detailing the key qualification factors considered for every applicant."
            },
            {
                "id": "T2",
                "question_text": "Are job applicants explicitly notified prior to screening that an automated AI system will evaluate or rank their resume?",
                "guidance": "Check if applicants are served conspicuous disclosures prior to resume submission as required by NYC Local Law 144 and EU AI regulations.",
                "why_it_matters": "Failure to provide conspicuous automated employment decision notice results in statutory compliance fines and immediate legal liability.",
                "evidence_required": "Job application portal notice screenshot, applicant consent checkbox, terms of application disclosure.",
                "risk_category": "Statutory Notice Failure",
                "risk_severity": "Critical",
                "recommendation": "Embed an explicit disclosure checkbox on the career portal informing applicants that automated parsing and ranking will occur."
            },
            {
                "id": "T3",
                "question_text": "Are immutable audit logs maintained for every applicant evaluation, including input resume snapshot, model version, timestamp, and score?",
                "guidance": "Inspect whether your database records historical candidate evaluations, input snapshots, and ranking confidence for retrospective auditability.",
                "why_it_matters": "Without immutable audit trails, defending against wrongful termination or employment discrimination claims is forensic guesswork.",
                "evidence_required": "Immutable database audit log, resume snapshot archive, model version history.",
                "risk_category": "Audit Trail Absence",
                "risk_severity": "High",
                "recommendation": "Retain an immutable JSON record of each candidate's ingested features, model score, and evaluation timestamp for a minimum of 3 years."
            },
            {
                "id": "T4",
                "question_text": "Is model performance (e.g. interview conversion, post-hire performance) monitored periodically against hiring manager ground-truth feedback?",
                "guidance": "Assess whether AI resume rankings correlate positively with actual hiring manager interviews and successful probationary reviews.",
                "why_it_matters": "Unmonitored resume models experience concept drift, filtering out high-performing talent based on outdated keyword rules.",
                "evidence_required": "Hiring manager feedback surveys, correlation analysis of AI rank vs. job performance, drift telemetry.",
                "risk_category": "Concept Drift & False Rejection",
                "risk_severity": "Medium",
                "recommendation": "Conduct semi-annual reviews comparing initial AI applicant ranking scores against hiring manager interview outcomes."
            },
            {
                "id": "T5",
                "question_text": "Is a qualified human recruiter or hiring manager empowered to review and override all automated candidate rejection decisions?",
                "guidance": "Confirm whether adverse hiring actions require human sign-off with legitimate override authority rather than 100% automated rejection.",
                "why_it_matters": "Human oversight acts as the critical failsafe against automated hallucinations, atypical career trajectories, and algorithmic injustice.",
                "evidence_required": "Recruiter override audit trail, human reviewer sign-off workflow, override percentage telemetry.",
                "risk_category": "Unchecked Automated Rejection",
                "risk_severity": "Critical",
                "recommendation": "Enforce a mandatory recruiter review step for borderline candidate rejections before any final decline notice is dispatched."
            }
        ],
        "privacy": [
            {
                "id": "P1",
                "question_text": "Does your resume ingestion pipeline strip unnecessary candidate PII (e.g. phone numbers, home addresses, photos, national IDs) prior to inference?",
                "guidance": "Evaluate whether candidate resumes are scrubbed of non-job-related personal identifiers before qualification scoring.",
                "why_it_matters": "Processing extraneous personal data violates privacy laws and creates compounding data breach liability.",
                "evidence_required": "PII redaction pipeline code, sanitized resume sample files, redaction accuracy test results.",
                "risk_category": "PII Exposure & Resume Data Leak",
                "risk_severity": "Critical",
                "recommendation": "Implement an automated PII redaction layer that masks applicant contact numbers, home addresses, and personal emails before ranking."
            },
            {
                "id": "P2",
                "question_text": "Is access to candidate resumes, evaluation scores, and demographic analytics restricted via granular Role-Based Access Controls (RBAC) and MFA?",
                "guidance": "Review permissions to verify that only authorized hiring team members can view sensitive applicant portfolios and evaluation data.",
                "why_it_matters": "Permissive access to candidate databases exposes sensitive career and personal information to internal data leaks.",
                "evidence_required": "Applicant tracking system RBAC settings, MFA enforcement policy, recruiter access logs.",
                "risk_category": "Candidate Database Access Vulnerability",
                "risk_severity": "High",
                "recommendation": "Restrict applicant data viewing permissions to assigned hiring committee members and mandate MFA for all HR software logins."
            },
            {
                "id": "P3",
                "question_text": "Is there a defined, automated data retention and disposal schedule for unsuccessful candidate resumes and evaluation records?",
                "guidance": "Determine whether unsuccessful candidate data is securely purged after the statutory retention period (e.g. 12 or 24 months).",
                "why_it_matters": "Indefinite storage of candidate CVs and personal data violates GDPR/CCPA storage limitation principles.",
                "evidence_required": "Written candidate retention policy, automated purge cron script, data destruction certificates.",
                "risk_category": "Unlawful Resume Data Hoarding",
                "risk_severity": "High",
                "recommendation": "Establish an automated data purge deleting candidate resumes and personal notes 24 months post-application unless explicit talent pool consent is given."
            },
            {
                "id": "P4",
                "question_text": "Are all candidate resumes and evaluation scores encrypted both in transit (TLS 1.3) and at rest (AES-256) throughout the entire AI pipeline?",
                "guidance": "Verify cryptographic protection on applicant database volumes, file storage buckets, and intermediate embedding caches.",
                "why_it_matters": "Unencrypted candidate resumes expose sensitive employment history and identity documents to regulatory fines upon breach.",
                "evidence_required": "TLS cipher suite audit, cloud storage bucket encryption report, database encryption at rest settings.",
                "risk_category": "Cryptographic Non-Compliance",
                "risk_severity": "Critical",
                "recommendation": "Apply AES-256 encryption across all applicant resume storage repositories and enforce TLS 1.3 on all submission portals."
            },
            {
                "id": "P5",
                "question_text": "Does the organization maintain documented data governance procedures and vendor vetting for third-party resume parsing and scoring APIs?",
                "guidance": "Assess whether external AI APIs, cloud hosts, and proprietary candidate parsers undergo written data protection reviews.",
                "why_it_matters": "Employers are legally responsible for third-party AI vendors; unvetted tools can illegally train on proprietary applicant resumes.",
                "evidence_required": "Vendor Data Processing Agreements (DPA), third-party SOC2 / ISO 27001 certifications, vendor AI policy review.",
                "risk_category": "Third-Party Vendor Exposure",
                "risk_severity": "Medium",
                "recommendation": "Obtain written confirmation from third-party resume parsing vendors that customer resumes are never used for foundation model training."
            }
        ],
        "sustainability": [
            {
                "id": "S1",
                "question_text": "Does your engineering team track compute duration, GPU/CPU utilization, and estimated energy consumption for resume screening runs?",
                "guidance": "Check if runtime telemetry or cloud billing compute-hour metrics are monitored for AI batch candidate evaluations.",
                "why_it_matters": "Measuring energy usage is the necessary first step to minimizing carbon footprint and controlling cloud infrastructure costs.",
                "evidence_required": "Compute-hour telemetry reports, GPU utilization dashboard, monthly energy estimation sheet.",
                "risk_category": "Unmonitored Compute Energy",
                "risk_severity": "Medium",
                "recommendation": "Implement carbon telemetry tracking the kilowatt-hour consumption of batch resume parsing and ranking pipelines."
            },
            {
                "id": "S2",
                "question_text": "Are AI candidate evaluation computing resources optimized (e.g. batching resume processing, auto-scaling inference workers to zero when idle)?",
                "guidance": "Verify whether resume processing containers scale down to zero when no active job openings are accepting applicants.",
                "why_it_matters": "Idle GPU/cloud instances running during non-recruiting periods needlessly waste electrical energy and SME capital.",
                "evidence_required": "Container auto-scaling configuration, queue-based worker trigger policy, idle container audit.",
                "risk_category": "Idle Compute Inefficiency",
                "risk_severity": "Medium",
                "recommendation": "Configure queue-driven workers that scale candidate evaluation containers to zero when the incoming resume queue is empty."
            },
            {
                "id": "S3",
                "question_text": "Does the candidate parsing system avoid redundant computations by caching common skill embeddings and pre-extracted resume entities?",
                "guidance": "Confirm whether recurring skill taxonomies and job description embeddings hit a fast cache rather than re-running deep transformer models.",
                "why_it_matters": "Redundant re-computation of common skills and job profiles multiplies carbon footprint and cloud API costs.",
                "evidence_required": "Embedding cache architecture, cache hit ratio telemetry, redundant computation audit.",
                "risk_category": "Redundant Computation Waste",
                "risk_severity": "Low",
                "recommendation": "Deploy a Redis cache for standard skill and degree embeddings to eliminate repeated transformer inferences on duplicate qualifications."
            },
            {
                "id": "S4",
                "question_text": "Have your engineers evaluated lightweight classification models (e.g. gradient boosted trees, distilled models) rather than massive LLMs for resume matching?",
                "guidance": "Assess whether simpler, compact architectures were benchmarked against heavy foundation models for candidate qualification matching.",
                "why_it_matters": "Using massive generative LLMs for tasks solvable by lightweight tabular classifiers consumes 100x more energy for negligible gain.",
                "evidence_required": "Architecture benchmark report, energy-to-accuracy trade-off comparison, model selection rationale.",
                "risk_category": "Architectural Bloat",
                "risk_severity": "Medium",
                "recommendation": "Benchmark lightweight scikit-learn or LightGBM models against foundation models for candidate qualification matching."
            },
            {
                "id": "S5",
                "question_text": "Does the organization evaluate the regional carbon intensity and renewable energy factor of the cloud data centers hosting {app_name}?",
                "guidance": "Determine if candidate evaluation workloads are hosted in data centers with high renewable energy ratios.",
                "why_it_matters": "Executing identical batch resume runs in clean grid regions cuts operational greenhouse gas emissions by up to 70%.",
                "evidence_required": "Cloud region selection audit, data center carbon coefficient report, renewable grid migration plan.",
                "risk_category": "High-Carbon Grid Deployment",
                "risk_severity": "Low",
                "recommendation": "Select cloud regions with green grid commitments (e.g., Google Cloud us-central1 or AWS eu-north-1) for batch resume processing."
            }
        ]
    },

    # 3. HEALTHCARE & LIFE SCIENCES
    "healthcare": {
        "fairness": [
            {
                "id": "F1",
                "question_text": "Does your organization conduct clinical subgroup parity and performance testing across diverse patient demographic groups (age, gender, ethnicity, comorbidities) for {app_name}?",
                "guidance": "Assess whether training and validation cohorts adequately represent patient subgroups and whether sensitivity/specificity are balanced across demographics.",
                "why_it_matters": "Biased clinical AI models can produce higher false negative rates in underrepresented patient populations, resulting in delayed diagnosis and fatal health disparities.",
                "evidence_required": "Subgroup clinical performance report, demographic representation audit, sensitivity/specificity parity analysis across patient cohorts.",
                "risk_category": "Clinical Diagnostic Disparity",
                "risk_severity": "Critical",
                "recommendation": "Mandate stratified clinical validation measuring diagnostic sensitivity and false discovery rates across all patient demographic cohorts."
            },
            {
                "id": "F2",
                "question_text": "Are clinical outcome error rates and diagnostic suggestion disparities continuously evaluated across different hospital wards or patient demographics during clinical operation?",
                "guidance": "Evaluate whether real-world clinical suggestion acceptance and error rates are monitored monthly across patient populations to catch clinical bias drift.",
                "why_it_matters": "Models trained on tertiary hospital data frequently degrade when deployed across community or rural clinics with different patient baseline health.",
                "evidence_required": "Post-market clinical surveillance logs, subgroup complication tracking, monthly diagnostic parity reviews.",
                "risk_category": "Clinical Bias Drift",
                "risk_severity": "High",
                "recommendation": "Establish continuous clinical telemetry comparing automated diagnostic recommendations against attending physician final confirmed diagnoses."
            },
            {
                "id": "F3",
                "question_text": "Do you maintain an established reporting channel for clinicians, nurses, and patients to flag suspected diagnostic bias or erroneous automated triage?",
                "guidance": "Check if clinical staff and patients have a streamlined incident reporting mechanism to document unexpected or inappropriate clinical AI recommendations.",
                "why_it_matters": "Without an accessible clinical feedback channel, algorithmic diagnostic errors go uncorrected until adverse patient events or malpractice claims occur.",
                "evidence_required": "Clinical incident reporting protocol, patient grievance workflow, medical AI incident log.",
                "risk_category": "Clinical Redress Deficiency",
                "risk_severity": "High",
                "recommendation": "Integrate a 1-click clinical feedback flag in the Electronic Health Record (EHR) interface allowing doctors to document AI diagnostic disagreements."
            },
            {
                "id": "F4",
                "question_text": "Are healthcare proxy attributes (e.g. insurance status, zip code, primary language) audited to ensure they do not bias clinical triage or treatment recommendations?",
                "guidance": "Review whether your team maintains formal documentation verifying that socioeconomic proxies do not influence clinical care prioritization.",
                "why_it_matters": "Using insurance billing codes or postal codes as proxies can inadvertently deprioritize low-income patients for intensive medical interventions.",
                "evidence_required": "Clinical Model Card, proxy variable regression analysis, feature exclusion rationale.",
                "risk_category": "Socioeconomic Proxy Bias",
                "risk_severity": "High",
                "recommendation": "Exclude socioeconomic variables (insurance tier, billing category, postal code) from clinical triage and diagnostic suggestion models."
            },
            {
                "id": "F5",
                "question_text": "Does your organization have a formal clinical safety protocol and operational suspension threshold when diagnostic disparity exceeds clinical risk limits?",
                "guidance": "Determine if predefined clinical error triggers mandate an immediate operational pause and fallback to standard clinical care protocols.",
                "why_it_matters": "Detecting clinical bias is futile without a predetermined protocol to halt automated diagnostic suggestions before patient harm occurs.",
                "evidence_required": "Clinical safety protocol, operational suspension criteria, medical director oversight procedure.",
                "risk_category": "Clinical Safety Protocol Absence",
                "risk_severity": "Critical",
                "recommendation": "Implement an automated circuit-breaker that suspends AI clinical triage suggestions if false negative rates exceed 5% in any patient subgroup."
            }
        ],
        "transparency": [
            {
                "id": "T1",
                "question_text": "Can {app_name} provide clinically interpretable explanations (e.g. SHAP feature importances, medical imaging heatmaps) showing why a clinical recommendation was generated?",
                "guidance": "Verify if attending physicians can review which specific biomarker, vital sign, or clinical note triggered the recommendation.",
                "why_it_matters": "Clinicians cannot ethically or legally act on black-box diagnostic recommendations without understanding the underlying medical evidence.",
                "evidence_required": "Clinician explanation interface, SHAP feature attribution summary, medical imaging attention heatmaps.",
                "risk_category": "Black-Box Clinical Decisioning",
                "risk_severity": "Critical",
                "recommendation": "Deploy clinician-facing explanation panels displaying the top physiological biomarkers and clinical indicators supporting each AI suggestion."
            },
            {
                "id": "T2",
                "question_text": "Are patients explicitly notified when an AI or automated system has contributed to their clinical triage, diagnosis, or treatment plan?",
                "guidance": "Check if patients receive clear, accessible notice informing them of AI involvement in their care as mandated by healthcare transparency laws.",
                "why_it_matters": "Patient autonomy and medical ethics require informed consent and transparent disclosure of automated diagnostic tools.",
                "evidence_required": "Patient informed consent form, clinical AI notification disclosure document, EHR transparency badge.",
                "risk_category": "Patient Informed Consent Failure",
                "risk_severity": "High",
                "recommendation": "Include clear disclosure in patient intake materials and care summaries explaining the role of AI diagnostic assistance tools."
            },
            {
                "id": "T3",
                "question_text": "Are immutable, time-stamped audit logs maintained for every clinical AI inference, including patient input snapshot, model version, and confidence score?",
                "guidance": "Inspect whether your database records historical clinical inputs and model recommendations for retrospective medical audits and legal defense.",
                "why_it_matters": "Without immutable audit trails, defending against medical malpractice claims or regulatory investigations is forensic guesswork.",
                "evidence_required": "Immutable medical audit log, EHR inference history, write-once storage policy.",
                "risk_category": "Medical Audit Trail Absence",
                "risk_severity": "Critical",
                "recommendation": "Store an immutable, tamper-evident audit record in the EHR capturing patient vital inputs, AI recommendations, and model version."
            },
            {
                "id": "T4",
                "question_text": "Is clinical AI accuracy and calibration monitored periodically against post-operative findings, lab pathology ground truths, and physician diagnoses?",
                "guidance": "Assess whether diagnostic sensitivity, positive predictive value, and calibration curves are benchmarked quarterly against confirmed pathology reports.",
                "why_it_matters": "Clinical data drift and novel pathogen strains degrade model accuracy over time, leading to silent medical misdiagnoses.",
                "evidence_required": "Quarterly clinical calibration reports, pathology ground-truth comparison logs, diagnostic drift reports.",
                "risk_category": "Clinical Drift & Diagnostic Error",
                "risk_severity": "High",
                "recommendation": "Establish a quarterly review committee cross-referencing AI recommendations against confirmed lab pathology and surgical outcomes."
            },
            {
                "id": "T5",
                "question_text": "Is a licensed physician or qualified clinician mandated to review, validate, and sign off on all high-impact AI recommendations before clinical execution?",
                "guidance": "Confirm whether diagnostic suggestions, prescription recommendations, or triage escalations require human physician validation with full override authority.",
                "why_it_matters": "Autonomous clinical action without human oversight creates severe patient safety hazards and violates medical licensing regulations.",
                "evidence_required": "Doctor sign-off workflow, physician override logs, clinical protocol documentation.",
                "risk_category": "Autonomous Medical Action Hazard",
                "risk_severity": "Critical",
                "recommendation": "Enforce mandatory licensed physician electronic sign-off before any AI-generated clinical diagnosis or treatment order can be entered into the patient record."
            }
        ],
        "privacy": [
            {
                "id": "P1",
                "question_text": "Does your medical data pipeline enforce HIPAA / GDPR data minimization by de-identifying or removing direct patient identifiers (Safe Harbor 18 identifiers) prior to inference?",
                "guidance": "Evaluate whether patient names, medical record numbers, contact details, and dates are stripped or tokenized prior to AI model processing.",
                "why_it_matters": "Processing unmasked Protected Health Information (PHI) drastically magnifies HIPAA violation penalties and catastrophic patient privacy breach exposure.",
                "evidence_required": "HIPAA Safe Harbor de-identification script, PHI sanitization test logs, expert de-identification determination letter.",
                "risk_category": "PHI Breach & HIPAA Exposure",
                "risk_severity": "Critical",
                "recommendation": "Deploy automated HIPAA Safe Harbor de-identification stripping names, MRNs, and full dates before routing data to AI models."
            },
            {
                "id": "P2",
                "question_text": "Is access to patient clinical datasets, model weights, and inference logs restricted via granular Role-Based Access Controls (RBAC), least-privilege, and biometric/hardware MFA?",
                "guidance": "Review permissions to verify that only authorized clinical personnel can view patient records and model inference outputs.",
                "why_it_matters": "Permissive access to electronic medical records is the leading root cause of healthcare cybersecurity breaches and insider leaks.",
                "evidence_required": "EHR RBAC settings, clinical staff MFA audit, access audit logging report.",
                "risk_category": "Patient Record Access Vulnerability",
                "risk_severity": "Critical",
                "recommendation": "Enforce biometric or hardware token MFA for all clinical staff accessing AI diagnostic interfaces and implement automated session timeouts."
            },
            {
                "id": "P3",
                "question_text": "Is there a defined, automated retention and disposal schedule for temporary patient feature caches, inference telemetry, and training snapshots?",
                "guidance": "Determine whether temporary clinical cache files and intermediate model tensors are securely deleted immediately following inference completion.",
                "why_it_matters": "Indefinite storage of unpurged clinical telemetry creates latent medical privacy vulnerabilities and violates data protection standards.",
                "evidence_required": "Healthcare data retention schedule, ephemeral cache deletion script, cryptographic wipe certificates.",
                "risk_category": "Unlawful Medical Data Retention",
                "risk_severity": "High",
                "recommendation": "Implement ephemeral in-memory processing that cryptographically wipes intermediate patient feature vectors immediately upon inference output."
            },
            {
                "id": "P4",
                "question_text": "Are all Protected Health Information (PHI) and clinical model weights encrypted both in transit (TLS 1.3 with FIPS ciphers) and at rest (AES-256) throughout the entire AI pipeline?",
                "guidance": "Verify cryptographic protection across hospital networks, database volumes, cloud PACS storage buckets, and inference cache files.",
                "why_it_matters": "Unencrypted PHI in transit or at rest violates statutory HIPAA Security Rule mandates and triggers mandatory HHS breach reporting.",
                "evidence_required": "FIPS 140-2 cryptographic verification, TLS 1.3 cipher audit, database volume encryption certificate.",
                "risk_category": "Cryptographic Non-Compliance",
                "risk_severity": "Critical",
                "recommendation": "Configure AES-256 encryption at rest on all clinical database volumes and enforce TLS 1.3 across all medical device endpoints."
            },
            {
                "id": "P5",
                "question_text": "Does the organization execute formal Business Associate Agreements (BAA), Privacy Impact Assessments (PIA), and third-party security audits for external AI API vendors?",
                "guidance": "Assess whether third-party cloud hosts and medical AI algorithms have executed signed HIPAA BAAs and undergone written privacy impact reviews.",
                "why_it_matters": "Using medical AI cloud APIs without executed BAAs is an automatic federal HIPAA violation with severe civil monetary penalties.",
                "evidence_required": "Executed HIPAA Business Associate Agreements, third-party SOC2 Type II reports, completed healthcare PIA.",
                "risk_category": "Third-Party Vendor Exposure",
                "risk_severity": "Critical",
                "recommendation": "Execute formal HIPAA Business Associate Agreements with all third-party AI cloud vendors guaranteeing zero PHI retention."
            }
        ],
        "sustainability": [
            {
                "id": "S1",
                "question_text": "Does your clinical engineering team track compute duration, GPU utilization, and estimated electrical consumption for training and running {app_name}?",
                "guidance": "Check if runtime telemetry and compute-hour power draw are monitored for clinical diagnostic inference servers and model updates.",
                "why_it_matters": "Tracking healthcare IT compute power is essential for healthcare systems seeking to reduce Scope 2 hospital emissions and cloud operational spend.",
                "evidence_required": "Clinical cluster power telemetry, GPU compute-hour logs, monthly hospital sustainability reports.",
                "risk_category": "Unmonitored Hospital Compute Energy",
                "risk_severity": "Low",
                "recommendation": "Monitor kilowatt-hour power draw on clinical inference servers and integrate compute metrics into the hospital sustainability dashboard."
            },
            {
                "id": "S2",
                "question_text": "Are clinical AI computing resources optimized (e.g. right-sizing high-memory GPU instances, dynamic scaling between day/night hospital shifts)?",
                "guidance": "Verify whether diagnostic inference capacity scales dynamically between daytime clinic hours and lower-volume overnight emergency shifts.",
                "why_it_matters": "Over-provisioned medical imaging clusters running 24/7 at peak capacity during low-volume night shifts waste substantial electric power.",
                "evidence_required": "Clinical server scaling schedule, instance right-sizing audit, off-peak utilization report.",
                "risk_category": "Hospital Compute Inefficiency",
                "risk_severity": "Low",
                "recommendation": "Configure dynamic autoscaling that reduces active clinical GPU workers during off-peak overnight hospital shifts."
            },
            {
                "id": "S3",
                "question_text": "Does the diagnostic system avoid redundant computation by caching patient medical imaging embeddings and recurring lab profile features?",
                "guidance": "Confirm whether recurring patient baseline data hits an in-memory cache rather than re-running compute-heavy neural transforms.",
                "why_it_matters": "Redundant re-processing of static patient imaging studies wastes electric power and adds unnecessary latency to clinical workflows.",
                "evidence_required": "Clinical feature cache architecture, cache hit telemetry, latency optimization report.",
                "risk_category": "Redundant Medical Computation",
                "risk_severity": "Low",
                "recommendation": "Implement an encrypted cache for static baseline medical imaging embeddings to eliminate repeated neural passes for longitudinal comparisons."
            },
            {
                "id": "S4",
                "question_text": "Have your engineers evaluated lightweight, quantized medical models (e.g. INT8 quantized networks, distilled vision models) over bloated foundation networks?",
                "guidance": "Assess whether compact clinical models were benchmarked against massive multi-billion parameter networks for routine diagnostic classification.",
                "why_it_matters": "Using massive foundation models for routine clinical classification tasks consumes 100x more energy for negligible diagnostic accuracy gain.",
                "evidence_required": "Model quantization benchmark report, clinical accuracy trade-off analysis, model selection documentation.",
                "risk_category": "Architectural Bloat",
                "risk_severity": "Medium",
                "recommendation": "Quantize clinical neural networks to INT8 or deploy distilled models to achieve 4x energy reduction while preserving diagnostic sensitivity."
            },
            {
                "id": "S5",
                "question_text": "Does the organization evaluate the regional carbon intensity and renewable energy factor of the cloud data centers hosting clinical AI workloads?",
                "guidance": "Determine if medical AI workloads are hosted in data centers with high renewable energy ratios.",
                "why_it_matters": "Hosting hospital AI workloads in clean grid regions can cut operational greenhouse gas emissions by up to 70%.",
                "evidence_required": "Healthcare cloud region selection policy, data center carbon coefficient report, renewable grid migration plan.",
                "risk_category": "High-Carbon Grid Deployment",
                "risk_severity": "Low",
                "recommendation": "Select healthcare-compliant cloud regions powered by verified renewable energy grids for batch clinical analytics."
            }
        ]
    },

    # 4. BANKING & FINANCE
    "banking_finance": {
        "fairness": [
            {
                "id": "F1",
                "question_text": "Does your financial institution conduct pre-deployment disparate impact testing across protected demographic classes for {app_name}?",
                "guidance": "Assess whether training datasets and credit scoring/lending models have been tested for Equal Credit Opportunity Act (ECOA) compliance.",
                "why_it_matters": "Unchecked historical lending biases in training data translate directly into discriminatory credit decisions and severe federal regulatory enforcement.",
                "evidence_required": "ECOA disparate impact audit, Fair Lending testing report, demographic selection rate parity analysis.",
                "risk_category": "Fair Lending Violation & ECOA Exposure",
                "risk_severity": "Critical",
                "recommendation": "Execute formal disparate impact ratio audits across gender and racial groups prior to deploying automated credit decision models."
            },
            {
                "id": "F2",
                "question_text": "Are credit approval rates, interest rate spreads, and credit limit allocations continuously monitored for demographic parity drift?",
                "guidance": "Evaluate whether automated lending outcomes are monitored monthly to catch runtime fairness drift across customer demographic segments.",
                "why_it_matters": "Financial credit models frequently drift over economic cycles, resulting in disparate rejection rates or higher interest rate quotes for minority borrowers.",
                "evidence_required": "Monthly fair lending monitoring dashboard, approval rate distribution by demographic tier, rate spread variance reports.",
                "risk_category": "Lending Disparity Drift",
                "risk_severity": "High",
                "recommendation": "Implement automated monitoring tracking interest rate quotes and approval rates across demographic groups on a monthly cadence."
            },
            {
                "id": "F3",
                "question_text": "Do you maintain an established customer adverse action notice and dispute resolution channel for contested credit or loan denials?",
                "guidance": "Check if rejected loan or credit applicants receive clear adverse action notices and an accessible appeal mechanism as required by FCRA.",
                "why_it_matters": "Failing to provide clear adverse action reasons and dispute mechanisms violates the Fair Credit Reporting Act (FCRA) and invites CFPB penalties.",
                "evidence_required": "FCRA adverse action notice template, customer credit dispute workflow, appeal resolution log.",
                "risk_category": "FCRA Notice & Recourse Failure",
                "risk_severity": "High",
                "recommendation": "Automate the delivery of FCRA-compliant adverse action notices detailing specific reasons for credit denial with clear dispute contact information."
            },
            {
                "id": "F4",
                "question_text": "Are financial proxy attributes (e.g. zip code, retail store visited, phone type) audited to prevent digital redlining and indirect demographic discrimination?",
                "guidance": "Review whether your team maintains formal documentation verifying that geographic or consumer proxy variables do not reintroduce digital redlining.",
                "why_it_matters": "Using postal codes or merchant spending categories as proxies can quietly reintroduce prohibited racial or socioeconomic redlining into lending decisions.",
                "evidence_required": "Proxy variable correlation analysis, Fair Lending model card, feature exclusion justification.",
                "risk_category": "Digital Redlining & Proxy Bias",
                "risk_severity": "Critical",
                "recommendation": "Perform correlation testing on all alternative data features and exclude postal codes or geographic proxies that correlate with demographic traits."
            },
            {
                "id": "F5",
                "question_text": "Does your financial institution maintain a formal corrective action plan or operational pause trigger when fair lending disparity exceeds regulatory limits?",
                "guidance": "Determine if predefined disparity triggers mandate an immediate operational pause, underwriting re-weighting, or model retraining.",
                "why_it_matters": "Detecting disparate impact without an actionable remediation protocol leaves the institution exposed to severe regulatory fines and civil rights litigation.",
                "evidence_required": "Fair Lending remediation protocol, underwriting override criteria, board-approved corrective action plan.",
                "risk_category": "Remediation Protocol Absence",
                "risk_severity": "High",
                "recommendation": "Adopt a board-approved policy establishing mandatory underwriting review if the approval ratio between demographic groups falls below 0.80."
            }
        ],
        "transparency": [
            {
                "id": "T1",
                "question_text": "Can {app_name} generate individualized explanation factor codes (e.g. SHAP top negative drivers) justifying every automated credit decision?",
                "guidance": "Verify if underwriters and consumers can review the top 4 adverse factors that contributed to a credit denial or loan price spread.",
                "why_it_matters": "Black-box financial decisioning violates statutory FCRA and ECOA requirements that mandate actionable adverse action reason codes.",
                "evidence_required": "SHAP adverse action factor generator, underwriter explanation interface, consumer explanation notice sample.",
                "risk_category": "Adverse Action Reason Failure",
                "risk_severity": "Critical",
                "recommendation": "Generate the top 4 key adverse factor codes using local SHAP explanations for every credit application denied by the automated system."
            },
            {
                "id": "T2",
                "question_text": "Are customers explicitly notified when an AI or automated system has played a material role in underwriting, credit limit, or fraud decisions?",
                "guidance": "Check if loan seekers or account holders receive conspicuous disclosures that automated algorithms are utilized in evaluating their application.",
                "why_it_matters": "Consumer protection regulations strictly require transparent disclosure of automated financial decisioning systems.",
                "evidence_required": "Credit application disclosure screenshot, customer terms and conditions clause, automated underwriting notice.",
                "risk_category": "Financial Transparency Non-Compliance",
                "risk_severity": "High",
                "recommendation": "Include an upfront disclosure on all credit application portals stating that automated risk models evaluate qualification criteria."
            },
            {
                "id": "T3",
                "question_text": "Are immutable, tamper-evident audit logs maintained for every financial prediction, including applicant inputs, model version, timestamp, and score?",
                "guidance": "Inspect whether your database records historical credit inputs, model versions, and risk scores in a write-once tamper-evident ledger.",
                "why_it_matters": "Without immutable audit trails, defending against regulatory examinations (OCC, Fed, CFPB) or legal challenges is impossible.",
                "evidence_required": "Write-once audit ledger schema, historical decision snapshot database, model lineage documentation.",
                "risk_category": "Financial Audit Trail Absence",
                "risk_severity": "Critical",
                "recommendation": "Deploy a tamper-evident, append-only ledger recording all credit scoring inputs, model version IDs, and underwriting recommendations."
            },
            {
                "id": "T4",
                "question_text": "Is credit model performance (e.g. Gini coefficient, population stability index, default drift) monitored periodically against actual repayment data?",
                "guidance": "Assess whether the model's predictive power and feature distributions are benchmarked quarterly against actual loan delinquency and charge-off rates.",
                "why_it_matters": "Macroeconomic shifts degrade financial risk models, leading to severe undercapitalization, bad debt spikes, or unwarranted credit rationing.",
                "evidence_required": "Quarterly model validation reports, Population Stability Index (PSI) tracking, default rate calibration charts.",
                "risk_category": "Financial Model Risk & Population Drift",
                "risk_severity": "High",
                "recommendation": "Monitor the Population Stability Index (PSI) monthly and mandate model retraining if PSI exceeds 0.25 indicating severe distribution drift."
            },
            {
                "id": "T5",
                "question_text": "Is a qualified credit underwriter or risk officer empowered to review, validate, and override automated credit rejections or risk classifications?",
                "guidance": "Confirm whether high-value loans, borderline credit denials, or complex commercial underwriting decisions require human underwriter sign-off.",
                "why_it_matters": "Unassisted automated underwriting can trigger systemic portfolio risk, false denials, and catastrophic credit losses during market disruptions.",
                "evidence_required": "Underwriter manual review workflow, exception and override policy, underwriter override audit log.",
                "risk_category": "Autonomous Financial Action Hazard",
                "risk_severity": "Critical",
                "recommendation": "Enforce a mandatory human underwriter review workflow for all credit applications falling within a borderline risk buffer score."
            }
        ],
        "privacy": [
            {
                "id": "P1",
                "question_text": "Does your financial data pipeline enforce data minimization by tokenizing or masking sensitive financial identifiers (e.g. SSNs, account numbers, card numbers) prior to AI processing?",
                "guidance": "Evaluate whether personal identity numbers and full bank account credentials are tokenized into non-reversible IDs before model ingestion.",
                "why_it_matters": "Ingesting and storing unmasked financial PII creates severe PCI-DSS, GLBA, and banking secrecy regulatory breach liabilities.",
                "evidence_required": "Tokenization gateway architecture, PCI-DSS compliance report, financial PII masking test logs.",
                "risk_category": "Financial PII & PCI-DSS Violation",
                "risk_severity": "Critical",
                "recommendation": "Implement tokenization at the ingestion gateway so models only receive synthetic surrogate IDs rather than raw customer SSNs or account numbers."
            },
            {
                "id": "P2",
                "question_text": "Is access to customer financial data, credit scoring models, and underwriting logs restricted via zero-trust RBAC, least-privilege, and hardware MFA?",
                "guidance": "Review permissions to verify that only authorized credit analysts and risk officers can access sensitive customer financial statements.",
                "why_it_matters": "Permissive access to financial databases is the leading root cause of banking data leaks, insider fraud, and identity theft.",
                "evidence_required": "GLBA access control policy, hardware MFA enrollment logs, privileged account audit report.",
                "risk_category": "Financial Database Access Vulnerability",
                "risk_severity": "Critical",
                "recommendation": "Mandate hardware security token MFA for all credit database access and review privileged underwriter permissions quarterly."
            },
            {
                "id": "P3",
                "question_text": "Is there a defined, automated data retention and disposal schedule for customer loan inquiries, financial statements, and temporary feature vectors?",
                "guidance": "Determine whether customer financial application documents and temporary inference features are purged after statutory compliance retention periods.",
                "why_it_matters": "Indefinite retention of unredacted financial statements violates GLBA / privacy laws and compounds cybersecurity breach liabilities.",
                "evidence_required": "Financial data retention schedule, automated disposal policy, certificate of secure data destruction.",
                "risk_category": "Unlawful Financial Data Hoarding",
                "risk_severity": "High",
                "recommendation": "Establish an automated disposal schedule securely purging temporary credit application feature vectors 180 days post-underwriting decision."
            },
            {
                "id": "P4",
                "question_text": "Are all customer financial records, model parameters, and credit bureau data encrypted both in transit (TLS 1.3 with FIPS ciphers) and at rest (AES-256 with HSM)?",
                "guidance": "Verify cryptographic protection on core banking database volumes, bureau communication channels, and cloud storage volumes.",
                "why_it_matters": "Unencrypted financial data in transit or at rest triggers immediate mandatory regulatory enforcement and reputational collapse upon breach.",
                "evidence_required": "HSM key management policy, TLS 1.3 cipher report, database volume encryption certificate.",
                "risk_category": "Cryptographic Non-Compliance",
                "risk_severity": "Critical",
                "recommendation": "Apply AES-256 encryption managed via Cloud HSM on all financial databases and enforce TLS 1.3 on all bureau API integrations."
            },
            {
                "id": "P5",
                "question_text": "Does the financial institution maintain documented data governance procedures, vendor risk management (VRM) reviews, and SOC2 audits for AI service providers?",
                "guidance": "Assess whether third-party fintech APIs, credit bureaus, and cloud AI hosting providers undergo written security and compliance vetting.",
                "why_it_matters": "Financial institutions are legally responsible for third-party vendor breaches; using unvetted fintech AI tools exposes the bank to OCC sanctions.",
                "evidence_required": "Executed third-party vendor risk management (VRM) reviews, SOC2 Type II reports, vendor confidentiality agreements.",
                "risk_category": "Third-Party Vendor Exposure",
                "risk_severity": "High",
                "recommendation": "Require all external fintech and model hosting vendors to provide annual SOC2 Type II compliance reports and execute financial data processing addendums."
            }
        ],
        "sustainability": [
            {
                "id": "S1",
                "question_text": "Does your financial engineering team track compute duration, GPU utilization, and estimated energy consumption for running financial models?",
                "guidance": "Check if runtime telemetry or cloud billing compute-hour metrics are monitored for hosting automated credit scoring and fraud inference systems.",
                "why_it_matters": "Measuring energy usage is necessary to comply with ESG disclosures, reduce Scope 2 emissions, and eliminate wasteful cloud compute spend.",
                "evidence_required": "Financial cluster power telemetry, compute-hour dashboard, annual ESG energy consumption report.",
                "risk_category": "Unmonitored FinTech Energy",
                "risk_severity": "Low",
                "recommendation": "Integrate cloud compute energy telemetry into the institution's annual ESG sustainability report."
            },
            {
                "id": "S2",
                "question_text": "Are financial AI computing resources optimized (e.g. dynamic autoscaling outside market trading hours, right-sizing credit scoring clusters)?",
                "guidance": "Verify whether credit scoring and fraud analysis clusters scale down dynamically during non-trading or overnight customer hours.",
                "why_it_matters": "Idle financial cloud servers running 24/7 at peak capacity outside active customer transaction hours waste substantial electric power.",
                "evidence_required": "Fintech server auto-scaling policy, scheduled worker reduction script, instance right-sizing review.",
                "risk_category": "Resource Inefficiency",
                "risk_severity": "Low",
                "recommendation": "Configure dynamic scaling that reduces active credit scoring worker nodes by 50% outside standard banking business hours."
            },
            {
                "id": "S3",
                "question_text": "Does the system avoid unnecessary redundant processing by caching recurring customer credit bureau features and static demographic indices?",
                "guidance": "Confirm whether recurring customer bureau attributes and zip-code indices hit an in-memory cache rather than re-computing complex features.",
                "why_it_matters": "Redundant re-computation of static financial features multiplies power consumption and unnecessary third-party API query fees.",
                "evidence_required": "In-memory feature cache configuration, cache hit ratio telemetry, redundant computation audit.",
                "risk_category": "Redundant Financial Computation",
                "risk_severity": "Low",
                "recommendation": "Deploy an in-memory cache for static customer credit bureau features to eliminate redundant feature transformations within a 30-day window."
            },
            {
                "id": "S4",
                "question_text": "Have your engineers evaluated lightweight, interpretable tabular models (e.g. XGBoost, logistic regression, LightGBM) over massive deep neural networks?",
                "guidance": "Assess whether compact, explainable tabular architectures were benchmarked against heavy foundation models for credit scoring.",
                "why_it_matters": "Using massive deep learning networks for credit tabular classification consumes 50x more energy and creates explainability barriers for negligible accuracy gain.",
                "evidence_required": "Model architecture benchmark report, energy-to-accuracy trade-off analysis, model risk selection rationale.",
                "risk_category": "Architectural Bloat",
                "risk_severity": "Medium",
                "recommendation": "Standardize on lightweight, highly interpretable gradient boosted trees (LightGBM/XGBoost) for tabular credit risk modeling."
            },
            {
                "id": "S5",
                "question_text": "Does the organization evaluate the regional carbon intensity and renewable energy factor of the cloud data centers hosting its financial AI systems?",
                "guidance": "Determine if credit scoring workloads are hosted in data centers with high renewable energy ratios.",
                "why_it_matters": "Hosting financial AI systems in clean grid regions can cut operational greenhouse gas emissions by up to 70%.",
                "evidence_required": "Cloud region sustainability audit, data center PUE and carbon factor report, green data center migration plan.",
                "risk_category": "High-Carbon Grid Deployment",
                "risk_severity": "Low",
                "recommendation": "Migrate persistent financial model inference workloads to cloud data centers with certified >80% renewable grid power."
            }
        ]
    },
    # 5. RETAIL & E-COMMERCE
    "retail_ecommerce": {
        "fairness": [
            {
                "id": "F1",
                "question_text": "Does your organization conduct pre-deployment parity audits on dynamic pricing and personalized promotion algorithms across customer demographics and geographic regions for {app_name}?",
                "guidance": "Examine whether discount allocations, promotional pricing, or personalized cart offers yield systematic disparities across postal codes, socioeconomic groups, or customer segments.",
                "why_it_matters": "Algorithmic price discrimination or unequal discount distribution damages customer trust and risks scrutiny under fair trade and consumer protection regulations.",
                "evidence_required": "Pricing disparity audit reports, demographic discount distribution analysis, regional promotional fairness testing logs.",
                "risk_category": "Algorithmic Price Discrimination",
                "risk_severity": "Critical",
                "recommendation": "Perform Fairlearn demographic parity evaluations on discount algorithms to guarantee uniform promotional access across customer cohorts."
            },
            {
                "id": "F2",
                "question_text": "Are personalized product recommendations continuously evaluated to prevent gender, age, or income stereotyping?",
                "guidance": "Assess whether product suggestion rankings (e.g., luxury goods, essential items, financing options) are monitored to detect demographic echo chambers or biased categorization.",
                "why_it_matters": "Stereotypical recommendation loops restrict consumer choice, limit commercial exposure, and perpetuate biased buying assumptions.",
                "evidence_required": "Recommendation ranking audit by demographic group, category diversity metrics, catalog coverage distribution reports.",
                "risk_category": "Recommender Stereotyping",
                "risk_severity": "High",
                "recommendation": "Integrate serendipity and diversity re-ranking algorithms to balance personalized product recommendations across diverse categories."
            },
            {
                "id": "F3",
                "question_text": "Is there a formal dispute and review channel for shoppers who encounter automated order cancellations, account restrictions, or payment flags?",
                "guidance": "Verify if shoppers can appeal automated fraud blocks, false positive bot detections, or cancelled orders with human customer service.",
                "why_it_matters": "Uncontested automated account flags lock out legitimate shoppers and generate severe negative consumer sentiment.",
                "evidence_required": "Customer appeal workflow documentation, false-positive resolution SLA logs, customer service escalation guidelines.",
                "risk_category": "Unchecked Automated Disqualification",
                "risk_severity": "High",
                "recommendation": "Establish a 24-hour human review workflow for all automated order cancellations and suspected fraud flags."
            },
            {
                "id": "F4",
                "question_text": "Are customer behavioral proxy features (e.g., device model, postal code, browsing speed) and fairness trade-offs documented in a governance card?",
                "guidance": "Review whether your data science team maintains documentation detailing proxy features that could correlate with demographic or socioeconomic status.",
                "why_it_matters": "Hidden proxy features like device type or zip code can quietly re-introduce demographic bias into automated checkout offers.",
                "evidence_required": "Model cards, feature proxy risk evaluations, documentation of model optimization trade-offs.",
                "risk_category": "Proxy Feature Vulnerability",
                "risk_severity": "Medium",
                "recommendation": "Conduct a proxy correlation audit to remove features that correlate heavily (>0.7) with sensitive demographic attributes."
            },
            {
                "id": "F5",
                "question_text": "Does {biz_name} have a documented protocol to pause or retrain recommendation models when algorithmic disparity exceeds predefined thresholds?",
                "guidance": "Determine if predefined disparity triggers mandate an operational pause or fallback to popularity-based ranking when recommendations exhibit disparate impact.",
                "why_it_matters": "Detecting recommendation bias is useless without an actionable protocol to halt or remediate skewed merchandising algorithms.",
                "evidence_required": "Disparity incident response SOP, model rollback playbook, algorithmic containment runbook.",
                "risk_category": "Ungoverned Production Drift",
                "risk_severity": "High",
                "recommendation": "Implement an automated circuit-breaker that falls back to neutral top-seller ranking if disparity exceeds 15%."
            }
        ],
        "transparency": [
            {
                "id": "T1",
                "question_text": "Can {app_name} provide transparent explanations for why specific products, prices, or search results are ranked for an individual customer?",
                "guidance": "Check whether product detail pages or search interfaces disclose the primary factors (e.g., past browsing, category popularity, sponsored items) driving recommendations.",
                "why_it_matters": "Opaque recommendations cause customer frustration and conflict with emerging digital consumer transparency mandates.",
                "evidence_required": "Explanatory UI mockups, ranking factor documentation, global feature importance summaries.",
                "risk_category": "Black-Box Merchandising",
                "risk_severity": "Medium",
                "recommendation": "Add a transparent 'Why am I seeing this recommendation?' badge on personalized product carousels."
            },
            {
                "id": "T2",
                "question_text": "Are shoppers clearly notified when AI is being used to generate product descriptions, customer support responses, or personalized pricing?",
                "guidance": "Inspect whether conversational shopping assistants and AI-generated reviews display prominent disclosure banners.",
                "why_it_matters": "Failing to disclose automated AI interactions violates FTC guidelines, consumer protection standards, and the EU AI Act.",
                "evidence_required": "AI disclosure badges, chatbot disclaimer screenshots, published AI transparency policy.",
                "risk_category": "Consumer Deception Risk",
                "risk_severity": "High",
                "recommendation": "Display prominent 'AI-Powered Assistant' disclosure banners across all virtual shopping dialogues."
            },
            {
                "id": "T3",
                "question_text": "Are immutable logs maintained for automated customer decisions, including pricing changes, cart discounts, and fraud scores?",
                "guidance": "Verify if the platform archives inference inputs, timestamp, model ID, and output values for every automated pricing or fraud decision.",
                "why_it_matters": "Without immutable logs, resolving customer pricing disputes or defending against consumer audit inquiries is impossible.",
                "evidence_required": "Database audit trail configuration, schema documentation for decision logging, log retention policies.",
                "risk_category": "Forensic Unauditability",
                "risk_severity": "High",
                "recommendation": "Implement structured JSON event logging for every automated checkout quote and fraud risk determination."
            },
            {
                "id": "T4",
                "question_text": "Is model performance (e.g. click-through rate, conversion parity, search relevance) monitored continuously against ground truth customer outcomes?",
                "guidance": "Assess whether recommendation accuracy and customer purchase conversion are tracked continuously to detect performance degradation.",
                "why_it_matters": "Data drift and shifting seasonal purchasing habits degrade model performance, causing silent revenue drops and inappropriate recommendations.",
                "evidence_required": "Model monitoring dashboards, monthly accuracy tracking reports, data drift alerts.",
                "risk_category": "Unmonitored Model Decay",
                "risk_severity": "Medium",
                "recommendation": "Establish automated weekly drift reports measuring recommendation conversion rates against historical baselines."
            },
            {
                "id": "T5",
                "question_text": "Does a qualified human supervisor have the ability to review, adjust, or override automated merchandising and high-value fraud decisions?",
                "guidance": "Confirm whether store managers or fraud analysts can override automated cancellations or adjust algorithmic catalog rankings.",
                "why_it_matters": "Without human oversight, algorithmic errors or pricing glitches can trigger catastrophic inventory liquidation or customer churn.",
                "evidence_required": "Supervisor override interface documentation, manual adjustment audit logs, escalation protocols.",
                "risk_category": "Lack of Human Failsafe",
                "risk_severity": "Critical",
                "recommendation": "Empower customer support leads and fraud specialists with single-click manual override controls for all automated checkout flags."
            }
        ],
        "privacy": [
            {
                "id": "P1",
                "question_text": "Does the data ingestion pipeline strip or mask unnecessary personal identifiers (PII) before model training and inference in {app_name}?",
                "guidance": "Assess whether customer full names, payment card numbers, billing addresses, and device fingerprints are anonymized before recommendation modeling.",
                "why_it_matters": "Feeding raw consumer PII into recommendation engines exposes the SME to massive GDPR, CCPA, and PCI-DSS compliance penalties.",
                "evidence_required": "Data preprocessing pipeline scripts, tokenization architecture diagrams, PII audit reports.",
                "risk_category": "Data Minimization Violation",
                "risk_severity": "Critical",
                "recommendation": "Deploy an automated data masking layer to replace raw customer names and card tokens with pseudonymous UUIDs."
            },
            {
                "id": "P2",
                "question_text": "Is access to customer shopping histories, profiles, and recommendation weights restricted by granular Role-Based Access Controls (RBAC) and MFA?",
                "guidance": "Verify that customer browsing behavior, purchase records, and marketing lists are accessible only to authorized personnel.",
                "why_it_matters": "Permissive internal access creates severe insider threat vulnerability and exposes sensitive customer habits to breach.",
                "evidence_required": "RBAC policy matrix, user directory MFA enrollment logs, admin access audit trail.",
                "risk_category": "Privileged Access Exposure",
                "risk_severity": "High",
                "recommendation": "Enforce strict RBAC with mandatory MFA across all customer data warehouses and recommendation endpoints."
            },
            {
                "id": "P3",
                "question_text": "Is there a defined, automated data retention and disposal schedule for abandoned carts, guest checkout records, and browsing telemetry?",
                "guidance": "Determine whether inactive shopper sessions, cookie tracking logs, and temporary cart data are automatically purged after a reasonable business window.",
                "why_it_matters": "Indefinite hoarding of customer browsing telemetry violates privacy regulations and creates compounded data liability.",
                "evidence_required": "Data retention policy, automated TTL purge cron configurations, secure disposal verification logs.",
                "risk_category": "Unlawful Data Hoarding",
                "risk_severity": "High",
                "recommendation": "Implement an automated 90-day retention purge on ephemeral guest browsing logs and abandoned cart telemetry."
            },
            {
                "id": "P4",
                "question_text": "Are customer payment details, purchase records, and personal profiles encrypted both in transit (TLS 1.3) and at rest (AES-256)?",
                "guidance": "Verify cryptographic safeguards across all e-commerce database volumes, checkout APIs, and cloud cache layers.",
                "why_it_matters": "Unencrypted customer transactions and profiles expose {biz_name} to catastrophic breach liability and PCI decertification.",
                "evidence_required": "TLS configuration reports, storage encryption at rest certificates, database encryption audits.",
                "risk_category": "Inadequate Data Encryption",
                "risk_severity": "Critical",
                "recommendation": "Enforce TLS 1.3 for all checkout endpoints and verify AES-256 encryption at rest for customer databases."
            },
            {
                "id": "P5",
                "question_text": "Does {biz_name} maintain formal data processing agreements and privacy impact assessments for all third-party analytics, ad pixels, and AI APIs?",
                "guidance": "Assess whether third-party conversational AI tools, marketing trackers, and cloud recommendation providers undergo contractual privacy vetting.",
                "why_it_matters": "SMEs remain legally liable when third-party ad pixels or AI vendors unlawfully harvest shopper behavioral data.",
                "evidence_required": "Executed third-party DPAs, completed vendor security assessments, third-party script audit.",
                "risk_category": "Third-Party Vendor Privacy Leak",
                "risk_severity": "Medium",
                "recommendation": "Execute standard data protection agreements prohibiting third-party AI vendors from training on customer shopping queries."
            }
        ],
        "sustainability": [
            {
                "id": "S1",
                "question_text": "Does your engineering team track compute duration, GPU/CPU utilization, and carbon emissions for product recommendation training and catalog re-indexing?",
                "guidance": "Check if cloud billing compute hours and energy metrics are logged for embedding updates and recommender model retraining.",
                "why_it_matters": "Frequent model retraining over massive product catalogs incurs runaway cloud bills and unchecked carbon emissions.",
                "evidence_required": "Cloud compute billing reports, energy consumption telemetry logs, carbon tracking dashboard.",
                "risk_category": "Unmeasured Carbon Footprint",
                "risk_severity": "Medium",
                "recommendation": "Implement automated compute profiling tools (e.g. CodeCarbon) to measure energy consumption per recommendation batch."
            },
            {
                "id": "S2",
                "question_text": "Are e-commerce AI computing resources configured to auto-scale dynamically with traffic and scale down during off-peak hours?",
                "guidance": "Verify whether recommendation servers automatically scale to zero or minimal instances during low-traffic overnight hours.",
                "why_it_matters": "Static over-provisioning outside peak shopping events wastes significant energy and capital.",
                "evidence_required": "Autoscaling configuration files, cluster utilization heatmaps, off-peak instance provisioning logs.",
                "risk_category": "Over-Provisioned Idle Compute",
                "risk_severity": "Medium",
                "recommendation": "Configure Kubernetes Horizontal Pod Autoscalers to automatically scale recommender pods down during low-traffic periods."
            },
            {
                "id": "S3",
                "question_text": "Does {app_name} avoid redundant compute by caching top-selling recommendations and batching catalog embedding updates?",
                "guidance": "Confirm whether repeated product queries hit an in-memory Redis cache rather than recalculating recommendations on every pageview.",
                "why_it_matters": "Re-running real-time neural rankers for identical product pages multiplies energy consumption and degrades page load speed.",
                "evidence_required": "Redis/cache architecture documentation, cache hit ratio telemetry, batch inference scheduling scripts.",
                "risk_category": "Redundant Inference Compute",
                "risk_severity": "Low",
                "recommendation": "Implement a 15-minute Redis caching tier for top-ranking product recommendations to achieve a >80% cache hit rate."
            },
            {
                "id": "S4",
                "question_text": "Have your engineers benchmarked lightweight, efficient recommender architectures against oversized transformer foundation models?",
                "guidance": "Assess whether compact collaborative filtering, matrix factorization, or two-tower models were evaluated against multi-billion parameter LLMs.",
                "why_it_matters": "Deploying generative LLMs for basic product matching consumes 100x more energy for negligible recommendation improvement.",
                "evidence_required": "Recommender benchmark study, energy-to-accuracy trade-off report, model sizing rationale.",
                "risk_category": "Model Overparameterization",
                "risk_severity": "Medium",
                "recommendation": "Standardize on lightweight two-tower embedding or gradient boosted ranking models for catalog search and recommendations."
            },
            {
                "id": "S5",
                "question_text": "Does {biz_name} prioritize hosting its e-commerce AI workloads in cloud regions powered primarily by renewable energy?",
                "guidance": "Determine if recommendation endpoints are hosted in data center zones with high clean energy and low grid carbon factors.",
                "why_it_matters": "Migrating inference workloads to low-carbon cloud regions can reduce operational emissions by up to 70%.",
                "evidence_required": "Cloud region sustainability audit, data center carbon factor reports, green hosting roadmap.",
                "risk_category": "High-Carbon Cloud Hosting",
                "risk_severity": "Low",
                "recommendation": "Deploy production recommendation services in cloud data centers with certified >80% renewable power."
            }
        ]
    },
    # 6. GENERAL SME ENTERPRISE (Fallback for all SME domains)
    "general_sme": {
        "fairness": [
            {
                "id": "F1",
                "question_text": "Does {biz_name} conduct pre-deployment bias and demographic parity testing across user groups for {app_name}?",
                "guidance": "Assess whether training datasets and model outputs have been statistically tested for outcome disparities across protected groups or user cohorts.",
                "why_it_matters": "Unchecked historical biases in training data translate directly into discriminatory automated decisions, service allocations, or user experiences.",
                "evidence_required": "Pre-deployment fairness audit reports, demographic parity evaluations, disparity analysis logs.",
                "risk_category": "Algorithmic Bias & Disparity",
                "risk_severity": "Critical",
                "recommendation": "Conduct statistical parity tests using Fairlearn to identify outcome disparities across user demographics before deployment."
            },
            {
                "id": "F2",
                "question_text": "Are group outcome metrics (such as demographic parity ratio or equal opportunity difference) continuously monitored during operational use?",
                "guidance": "Evaluate whether automated recommendation rates and operational decisions are monitored on a recurring schedule to catch runtime bias drift.",
                "why_it_matters": "Models that appear balanced in development often experience disparate outcomes when deployed across changing real-world conditions.",
                "evidence_required": "Runtime bias monitoring dashboards, monthly fairness tracking reports, threshold alert configurations.",
                "risk_category": "Runtime Bias Drift",
                "risk_severity": "High",
                "recommendation": "Establish continuous monthly bias tracking to verify demographic parity ratio remains between 0.80 and 1.25."
            },
            {
                "id": "F3",
                "question_text": "Do you have an established reporting and appeal mechanism for users or stakeholders to challenge suspected unfair automated decisions?",
                "guidance": "Check if a clear contact method, appeal form, or human review channel exists for disputed automated recommendations or decisions.",
                "why_it_matters": "Without an accessible feedback or dispute mechanism, algorithmic harms remain invisible until complaints, customer churn, or lawsuits occur.",
                "evidence_required": "Published appeal process documentation, dispute resolution logs, customer appeal SLAs.",
                "risk_category": "Unchecked Algorithmic Disqualification",
                "risk_severity": "High",
                "recommendation": "Deploy a straightforward appeal form allowing users to request human review of any automated decision within 48 hours."
            },
            {
                "id": "F4",
                "question_text": "Are protected attributes, proxy features, and model fairness trade-offs documented in a formal model governance card?",
                "guidance": "Review whether your team maintains formal documentation detailing potential proxy variables and fairness trade-off rationales.",
                "why_it_matters": "Proxy variables like postal code or language style can reintroduce demographic bias; transparent documentation ensures accountability.",
                "evidence_required": "Model cards, feature proxy correlation matrices, fairness trade-off documentation.",
                "risk_category": "Proxy Variable Vulnerability",
                "risk_severity": "Medium",
                "recommendation": "Maintain a comprehensive Model Card documenting training data demographics, known limitations, and proxy risk assessments."
            },
            {
                "id": "F5",
                "question_text": "Does {biz_name} have a formal, documented corrective action plan or retraining threshold when algorithmic disparity exceeds acceptable limits?",
                "guidance": "Determine if predefined disparity triggers mandate an operational pause or model retraining when outcomes diverge systematically.",
                "why_it_matters": "Identifying bias is useless without a predetermined protocol to halt or remediate discriminatory automated workflows.",
                "evidence_required": "Bias remediation SOP, emergency model rollback playbook, retraining runbook.",
                "risk_category": "Lack of Remediation Protocol",
                "risk_severity": "High",
                "recommendation": "Create a clear governance SOP that triggers an automatic operational pause if disparity metrics exceed tolerance thresholds."
            }
        ],
        "transparency": [
            {
                "id": "T1",
                "question_text": "Can {app_name} provide local and global explanations (e.g. SHAP values, feature importance) for why a specific automated decision was reached?",
                "guidance": "Verify if operators and affected individuals can inspect which input features influenced a specific automated prediction or recommendation.",
                "why_it_matters": "Black-box models leave teams unable to justify automated actions to customers, management, or regulatory auditors.",
                "evidence_required": "SHAP/LIME explanation dashboards, feature importance documentation, sample decision explanation logs.",
                "risk_category": "Black-Box Decision Opacity",
                "risk_severity": "High",
                "recommendation": "Integrate SHAP tree or kernel explainers to output top contributing factors alongside every automated decision."
            },
            {
                "id": "T2",
                "question_text": "Are affected individuals explicitly notified when an AI or automated system has played a material role in a decision that impacts them?",
                "guidance": "Check if users interacting with {app_name} receive clear disclosure that recommendations, assessments, or outputs are AI-generated.",
                "why_it_matters": "Emerging AI governance laws and global consumer protection standards mandate clear disclosure when consumers interact with automated AI agents.",
                "evidence_required": "User interface disclaimers, terms of service AI disclosures, automated notification templates.",
                "risk_category": "Lack of AI Disclosure",
                "risk_severity": "High",
                "recommendation": "Add a prominent notice across user interfaces clearly indicating AI involvement in decision workflows."
            },
            {
                "id": "T3",
                "question_text": "Are immutable audit logs maintained for every automated prediction, including input snapshot, model version, timestamp, and confidence score?",
                "guidance": "Inspect whether your database records historical inputs, model version, timestamp, and outputs for retrospective auditability.",
                "why_it_matters": "Without audit trails, defending against customer disputes, compliance inquiries, or system errors is forensic guesswork.",
                "evidence_required": "Audit log database schema, sample immutable log entries, append-only log configuration.",
                "risk_category": "Inadequate Audit Trails",
                "risk_severity": "High",
                "recommendation": "Configure an append-only audit log capturing timestamp, model version, inputs, outputs, and confidence scores for every inference."
            },
            {
                "id": "T4",
                "question_text": "Is model performance (e.g. accuracy, error rates, data drift) monitored periodically against ground-truth feedback?",
                "guidance": "Assess whether prediction accuracy and input data distributions are benchmarked on a recurring basis against actual operational outcomes.",
                "why_it_matters": "Data drift and shifting operational conditions degrade model accuracy over time, leading to silent failures and degraded business performance.",
                "evidence_required": "Model monitoring dashboards, quarterly performance review reports, data drift alert logs.",
                "risk_category": "Silent Model Degradation",
                "risk_severity": "Medium",
                "recommendation": "Schedule quarterly model accuracy and data drift reviews comparing predictions against ground-truth business outcomes."
            },
            {
                "id": "T5",
                "question_text": "Is a qualified human-in-the-loop (HITL) empowered to review, validate, or override high-impact automated decisions before execution?",
                "guidance": "Confirm whether high-stakes decisions, high-value operations, or severe actions require human review and legitimate override authority.",
                "why_it_matters": "Human oversight acts as the critical failsafe against automated hallucinations, data errors, and catastrophic unintended consequences.",
                "evidence_required": "Human-in-the-loop workflow diagram, operator override logs, authorization matrix.",
                "risk_category": "Absence of Human Oversight",
                "risk_severity": "Critical",
                "recommendation": "Mandate explicit human supervisor approval for all automated decisions classified as high impact."
            }
        ],
        "privacy": [
            {
                "id": "P1",
                "question_text": "Does your data ingestion pipeline enforce data minimization by screening and stripping unnecessary personal identifiers (PII) before model processing?",
                "guidance": "Evaluate whether personal identifiers, contact numbers, government IDs, and payment details are masked or discarded prior to inference in {app_name}.",
                "why_it_matters": "Storing and processing extraneous PII drastically magnifies GDPR, CCPA, and data breach liabilities.",
                "evidence_required": "Data preprocessing scripts, PII anonymization configs, privacy audit reports.",
                "risk_category": "PII Exposure & Privacy Breach",
                "risk_severity": "Critical",
                "recommendation": "Implement an automated PII detection and masking filter prior to storing or processing data in AI workflows."
            },
            {
                "id": "P2",
                "question_text": "Is access to AI training datasets, model weights, and inference logs restricted via granular Role-Based Access Controls (RBAC) and MFA?",
                "guidance": "Review permissions to verify that only authorized personnel can access sensitive operational datasets or customer records.",
                "why_it_matters": "Permissive internal access and shared credentials are leading root causes of data leaks and insider threats.",
                "evidence_required": "RBAC role definitions, MFA enforcement policies, access review records.",
                "risk_category": "Inadequate Access Control",
                "risk_severity": "High",
                "recommendation": "Enforce Role-Based Access Controls and multi-factor authentication for all systems containing operational or training data."
            },
            {
                "id": "P3",
                "question_text": "Is there a defined, automated data retention and disposal schedule for datasets collected and processed by {app_name}?",
                "guidance": "Determine whether temporary inquiry logs, operational inputs, and legacy records are securely purged after a defined retention period.",
                "why_it_matters": "Indefinite data hoarding violates privacy regulations and creates compounding litigation and cyber liability.",
                "evidence_required": "Data retention policy, automated deletion scripts, certificate of data destruction logs.",
                "risk_category": "Unlawful Data Retention",
                "risk_severity": "High",
                "recommendation": "Establish and automate a data retention policy with scheduled purging of operational logs older than statutory requirements."
            },
            {
                "id": "P4",
                "question_text": "Are all sensitive data fields encrypted both in transit (TLS 1.3) and at rest (AES-256) throughout the entire AI pipeline?",
                "guidance": "Verify cryptographic protection on database volumes, network communications, cloud storage buckets, and intermediate caching layers.",
                "why_it_matters": "Unencrypted data stores and communication channels expose {biz_name} to immediate regulatory sanctions upon breach.",
                "evidence_required": "TLS configuration certificates, database encryption at rest configs, cloud storage bucket policies.",
                "risk_category": "Unencrypted Sensitive Data",
                "risk_severity": "Critical",
                "recommendation": "Verify end-to-end encryption using TLS 1.3 for data in transit and AES-256 for all persistent storage."
            },
            {
                "id": "P5",
                "question_text": "Does {biz_name} maintain documented data governance procedures, privacy impact assessments (PIA), and vendor third-party vetting for AI tools?",
                "guidance": "Assess whether third-party conversational AI APIs, cloud hosts, and software sub-processors undergo written data protection and confidentiality reviews.",
                "why_it_matters": "SMEs are legally accountable for third-party sub-processors; using unvetted AI APIs can leak proprietary and customer data.",
                "evidence_required": "Third-party vendor assessments, signed Data Processing Agreements (DPAs), vendor privacy checklist.",
                "risk_category": "Third-Party Subprocessor Risk",
                "risk_severity": "Medium",
                "recommendation": "Require signed Data Processing Agreements with third-party AI vendors ensuring data is not stored or used for foundational model training."
            }
        ],
        "sustainability": [
            {
                "id": "S1",
                "question_text": "Does {biz_name} track compute duration, GPU/CPU utilization, and estimated energy consumption for model training and batch inference runs in {app_name}?",
                "guidance": "Check if runtime telemetry or cloud billing compute-hour metrics are monitored for hosting AI workloads.",
                "why_it_matters": "You cannot reduce carbon impact or optimize runaway cloud compute costs without measuring baseline energy consumption.",
                "evidence_required": "Cloud compute billing metrics, energy consumption tracking logs, carbon estimation reports.",
                "risk_category": "Unmeasured Compute Carbon Footprint",
                "risk_severity": "Medium",
                "recommendation": "Track GPU and CPU compute hours and calculate operational carbon emissions using standard emission conversion factors."
            },
            {
                "id": "S2",
                "question_text": "Are AI computing resources optimized (e.g. right-sizing cloud instances, auto-scaling to zero when idle, leveraging spot instances)?",
                "guidance": "Verify if AI inference servers scale down during non-business hours or dynamically match actual incoming workload demands.",
                "why_it_matters": "Idle GPU/cloud instances outside active operating hours generate unnecessary carbon emissions and drain SME operating capital.",
                "evidence_required": "Cloud autoscaling policies, idle compute shutdown scripts, instance sizing audits.",
                "risk_category": "Idle Compute Energy Waste",
                "risk_severity": "Medium",
                "recommendation": "Implement auto-scaling policies to scale inference instances down or to zero during prolonged idle periods."
            },
            {
                "id": "S3",
                "question_text": "Does {app_name} avoid unnecessary redundant processing by caching inference results and executing batched evaluations where applicable?",
                "guidance": "Confirm whether repetitive identical queries hit a low-latency cache rather than re-running deep model inference.",
                "why_it_matters": "Redundant re-computation wastes electric power and multiplies API token/inference expenses.",
                "evidence_required": "Cache layer architecture, cache hit rate telemetry, batch processing job schedules.",
                "risk_category": "Redundant Inference Computation",
                "risk_severity": "Low",
                "recommendation": "Implement response caching for common model queries to reduce unnecessary repetitive API calls and server compute."
            },
            {
                "id": "S4",
                "question_text": "Have your engineers evaluated lightweight, energy-efficient model architectures (e.g. distilled models, quantization, classical ML) before choosing heavy foundation models?",
                "guidance": "Assess whether compact models were benchmarked against massive multi-billion parameter networks for routine tasks.",
                "why_it_matters": "Using massive LLMs or oversized transformers for routine classification tasks consumes 100x more energy for negligible accuracy gain.",
                "evidence_required": "Model selection evaluation report, benchmark comparisons of model size vs accuracy, model quantization logs.",
                "risk_category": "Excessive Model Complexity",
                "risk_severity": "Medium",
                "recommendation": "Evaluate smaller, quantized, or domain-specialized models before deploying large foundation models for routine tasks."
            },
            {
                "id": "S5",
                "question_text": "Does {biz_name} evaluate the regional carbon intensity and renewable energy factor of the cloud data centers hosting its AI workloads?",
                "guidance": "Determine if cloud workloads are hosted in data centers with low carbon grid factors (e.g., regions powered by hydro/solar/nuclear).",
                "why_it_matters": "Hosting AI workloads in a clean grid region can cut actual operational greenhouse gas emissions by up to 70%.",
                "evidence_required": "Cloud region selection documentation, data center renewable energy certificates, region carbon intensity analysis.",
                "risk_category": "High Carbon Grid Deployment",
                "risk_severity": "Low",
                "recommendation": "Deploy or migrate AI workloads to cloud data centers in regions with a high percentage of renewable energy."
            }
        ]
    }
}

def generate_industry_assessment(
    business: Business,
    application: AIApplication,
    force_llm: bool = False
) -> List[QuestionDefinition]:
    """
    Core Dynamic Assessment Engine:
    Selects or generates a tailored 20-question suite across the 4 governance dimensions
    (Fairness, Transparency, Privacy, Sustainability) specific to the business profile,
    industry sector, AI purpose, processed data types, automated decision impact, and human oversight level.
    """
    industry_key = detect_industry_key(business.industry, application.business_function)
    
    # 1. Attempt LLM enhancement if GEMINI_API_KEY is configured and user requests or default enabled
    if force_llm or (settings.GEMINI_API_KEY and os.getenv("ENABLE_LLM_DYNAMIC_QUESTIONS", "false").lower() == "true"):
        llm_questions = try_generate_llm_custom_questions(business, application, industry_key)
        if llm_questions and len(llm_questions) == 20:
            return llm_questions

    # 2. High-fidelity Curated Engine with Metadata Interpolation
    bank = INDUSTRY_QUESTION_BANKS.get(industry_key)
    if not bank:
        # Fallback to general SME bank
        bank = INDUSTRY_QUESTION_BANKS.get("general_sme") or INDUSTRY_QUESTION_BANKS["automotive_services"]

    questions: List[QuestionDefinition] = []
    
    dimension_map = [
        ("fairness", "Fairness & Equity"),
        ("transparency", "Transparency & Explainability"),
        ("privacy", "Data Privacy & Governance"),
        ("sustainability", "Green AI & Sustainability")
    ]

    # Context values for string interpolation
    ctx = {
        "app_name": application.name or "the AI System",
        "biz_name": business.name or "the Enterprise",
        "industry": business.industry or "Commercial Services",
        "location": business.location or "Global",
        "data_types": application.data_types or "Operational records",
        "purpose": application.purpose or "automated operations"
    }

    is_high_impact = (application.automated_decision_impact or "").lower() == "high"
    is_unassisted = (application.human_oversight or "").lower() == "none"

    def _safe_format(template_str: str, context: dict) -> str:
        if not template_str:
            return ""
        try:
            return template_str.format(**context)
        except Exception:
            res = str(template_str)
            for k, v in context.items():
                res = res.replace(f"{{{k}}}", str(v))
            return res

    for cat_id, cat_title in dimension_map:
        cat_templates = bank.get(cat_id, [])
        for t in cat_templates:
            # Interpolate application specific metadata into templates safely
            q_text = _safe_format(t.get("question_text", ""), ctx)
            guidance = _safe_format(t.get("guidance", ""), ctx)
            why_it_matters = _safe_format(t.get("why_it_matters", ""), ctx)
            evidence = _safe_format(t.get("evidence_required", ""), ctx)
            rec = _safe_format(t.get("recommendation", ""), ctx)
            sev = t.get("risk_severity", "High")

            # Dynamic risk severity adjustment based on operational profile
            if is_high_impact and is_unassisted and t["id"] in ["F1", "T5", "P1", "P4"]:
                sev = "Critical"

            q_obj = QuestionDefinition(
                id=t["id"],
                category=cat_id,
                category_title=cat_title,
                industry=business.industry or "General SME",
                ai_application_context=f"{application.name} ({application.business_function or 'Production AI'})",
                question_text=q_text,
                why_it_matters=why_it_matters,
                guidance=guidance,
                evidence_required=evidence,
                risk_category=t.get("risk_category", f"{cat_title} Risk"),
                risk_severity=sev,
                answer_options=["Yes", "Partially", "No", "N/A"],
                recommendation=rec
            )
            questions.append(q_obj)

    return questions

def try_generate_llm_custom_questions(
    business: Business,
    application: AIApplication,
    industry_key: str
) -> Optional[List[QuestionDefinition]]:
    """
    Calls Google Gemini API to synthesize bespoke industry and application questions
    when GEMINI_API_KEY is configured.
    """
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an expert Responsible AI auditor. Generate exactly 20 customized AI governance assessment questions (5 for Fairness, 5 for Transparency, 5 for Data Privacy, 5 for Green AI/Sustainability) tailored to this specific SME profile:
- Business: {business.name}
- Industry: {business.industry}
- Location: {business.location}
- AI Application: {application.name}
- Purpose: {application.purpose}
- Business Function: {application.business_function}
- Data Types: {application.data_types}
- Automated Decision Impact: {application.automated_decision_impact}
- Human Oversight: {application.human_oversight}

Return JSON with a list of 20 objects. Each object must have:
"id": ("F1" to "F5", "T1" to "T5", "P1" to "P5", "S1" to "S5"),
"category": ("fairness", "transparency", "privacy", "sustainability"),
"category_title": ("Fairness & Equity", "Transparency & Explainability", "Data Privacy & Governance", "Green AI & Sustainability"),
"question_text": Specific question referencing {business.industry} and {application.name},
"why_it_matters": Explanation of specific business/legal/harm consequence,
"guidance": Detailed audit inspection guidance,
"evidence_required": Concrete artifacts to inspect,
"risk_category": Specific risk name,
"risk_severity": ("Critical", "High", "Medium", "Low"),
"recommendation": Actionable remediation advice.
Respond ONLY with raw valid JSON without markdown fences.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

        data = json.loads(raw_text)
        if isinstance(data, dict) and "questions" in data:
            data = data["questions"]

        if isinstance(data, list) and len(data) == 20:
            parsed = []
            for item in data:
                parsed.append(QuestionDefinition(
                    id=item.get("id"),
                    category=item.get("category"),
                    category_title=item.get("category_title"),
                    industry=business.industry,
                    ai_application_context=application.name,
                    question_text=item.get("question_text"),
                    why_it_matters=item.get("why_it_matters"),
                    guidance=item.get("guidance"),
                    evidence_required=item.get("evidence_required"),
                    risk_category=item.get("risk_category"),
                    risk_severity=item.get("risk_severity", "High"),
                    answer_options=["Yes", "Partially", "No", "N/A"],
                    recommendation=item.get("recommendation")
                ))
            return parsed
    except Exception as e:
        print(f"[DynamicAssessmentEngine] LLM generation skipped or failed: {e}")
        return None

    return None
