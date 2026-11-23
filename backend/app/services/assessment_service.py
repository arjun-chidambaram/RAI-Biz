import json
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from ..models import Assessment, AssessmentResponse, Risk, Recommendation, Business, AIApplication
from ..schemas import QuestionDefinition, AssessmentCreate
from .dynamic_assessment_engine import generate_industry_assessment, detect_industry_key, get_supported_industries
from .risk_intelligence_engine import RiskIntelligenceEngine

QUESTIONS_CATALOG: List[QuestionDefinition] = [
    # FAIRNESS
    QuestionDefinition(
        id="F1",
        category="fairness",
        category_title="Fairness & Demographic Equity",
        question_text="Does your organization conduct pre-deployment bias and parity testing across demographic groups (e.g., gender, age, ethnicity) for this AI system?",
        guidance="Assess whether historical customer enquiry datasets, vehicle service records, or booking logs have been statistically tested for representation and outcome disparities.",
        why_it_matters="Unchecked historical biases in training data translate directly into discriminatory automated service package recommendations, pricing quotes, or appointment priority."
    ),
    QuestionDefinition(
        id="F2",
        category="fairness",
        category_title="Fairness & Demographic Equity",
        question_text="Are group outcome metrics (such as demographic parity ratio or equal opportunity difference) continuously evaluated during operational use?",
        guidance="Evaluate whether automated service recommendation rates and quote discounts are monitored on a recurring schedule to catch runtime bias drift across customer groups.",
        why_it_matters="Models that appear fair during offline testing often experience disparate recommendation rates when deployed across changing real-world customer demographics and vehicle tiers."
    ),
    QuestionDefinition(
        id="F3",
        category="fairness",
        category_title="Fairness & Demographic Equity",
        question_text="Do you have an established reporting mechanism for customers, vehicle owners, or shop staff to report suspected bias or unfair automated decisions?",
        guidance="Check if a clear contact method, appeal form, or manager review channel exists for disputed service quotes, cancellations, or biased recommendations.",
        why_it_matters="Without an accessible feedback or dispute mechanism, algorithmic harms and customer service disparities remain invisible until negative reviews, customer churn, or consumer complaints occur."
    ),
    QuestionDefinition(
        id="F4",
        category="fairness",
        category_title="Fairness & Demographic Equity",
        question_text="Are protected attributes, proxy features (e.g. customer postal code, neighborhood, vehicle luxury tier), and model fairness trade-offs documented in a model governance card?",
        guidance="Review whether your team maintains formal documentation detailing potential proxy variables and fairness trade-off rationales in pricing and service recommendations.",
        why_it_matters="Proxy variables like customer postal code or vehicle brand can quietly reintroduce demographic bias; transparent documentation ensures accountable architectural choices."
    ),
    QuestionDefinition(
        id="F5",
        category="fairness",
        category_title="Fairness & Demographic Equity",
        question_text="Does your organization have a formal, documented corrective action plan or retraining threshold when algorithmic disparity exceeds acceptable limits?",
        guidance="Determine if predefined disparity triggers mandate an operational pause, prompt re-weighting, or model retraining when recommendation rates diverge systematically.",
        why_it_matters="Identifying bias is useless without a predetermined protocol to halt or remediate discriminatory automated workflows in customer recommendations."
    ),

    # TRANSPARENCY
    QuestionDefinition(
        id="T1",
        category="transparency",
        category_title="Transparency & Explainability",
        question_text="Can your AI system provide local and global explanations (e.g. SHAP values, feature importance) for why a specific automated recommendation or decision was reached?",
        guidance="Verify if service advisors and vehicle owners can inspect which input features (e.g., paint condition, vehicle age, usage frequency) influenced a specific service package recommendation.",
        why_it_matters="Black-box recommendations leave service advisors unable to justify suggested automotive treatments to customers or consumer protection auditors."
    ),
    QuestionDefinition(
        id="T2",
        category="transparency",
        category_title="Transparency & Explainability",
        question_text="Are affected individuals explicitly notified when an AI or automated system has played a material role in a decision that impacts them?",
        guidance="Check if customers interacting with the online booking assistant or service kiosk receive clear disclosure that recommendations and appointment options are AI-generated.",
        why_it_matters="Emerging consumer protection and global regulations strictly mandate clear disclosure when consumers interact with automated AI agents."
    ),
    QuestionDefinition(
        id="T3",
        category="transparency",
        category_title="Transparency & Explainability",
        question_text="Are immutable audit logs maintained for every automated prediction, including input snapshot, model version, timestamp, and confidence score?",
        guidance="Inspect whether your database records historical customer inquiry inputs, vehicle details, recommended detailing packages, and pricing outputs for retrospective auditability.",
        why_it_matters="Without audit trails, defending against customer pricing disputes, service warranty claims, or recommendation errors is forensic guesswork."
    ),
    QuestionDefinition(
        id="T4",
        category="transparency",
        category_title="Transparency & Explainability",
        question_text="Is model performance (e.g. precision, recall, data drift, concept drift) monitored periodically against ground-truth feedback?",
        guidance="Assess whether recommendation accuracy and seasonal demand patterns are benchmarked monthly or quarterly against actual technician inspection findings and customer reviews.",
        why_it_matters="Data drift and seasonal shifts degrade model accuracy over time, leading to silent failures, inappropriate service recommendations, and degraded business performance."
    ),
    QuestionDefinition(
        id="T5",
        category="transparency",
        category_title="Transparency & Explainability",
        question_text="Is a qualified human-in-the-loop (HITL) empowered to review, validate, or override high-impact automated recommendations before execution?",
        guidance="Confirm whether high-value detailing quotes, complex paint restoration packages, or booking cancellations require service advisor review and legitimate override authority.",
        why_it_matters="Human oversight acts as the critical failsafe against automated hallucinations, incorrect pricing, and gross customer dissatisfaction."
    ),

    # PRIVACY
    QuestionDefinition(
        id="P1",
        category="privacy",
        category_title="Data Privacy & Governance",
        question_text="Does your data ingestion pipeline enforce data minimization by screening and stripping unnecessary personal identifiers (PII) before model processing?",
        guidance="Evaluate whether customer phone numbers, driver's licenses, vehicle registration/VIN details, and payment information are masked or discarded prior to inference.",
        why_it_matters="Storing and processing extraneous customer PII drastically magnifies GDPR, CCPA, and data breach liability."
    ),
    QuestionDefinition(
        id="P2",
        category="privacy",
        category_title="Data Privacy & Governance",
        question_text="Is access to AI training datasets, model weights, and inference logs restricted via granular Role-Based Access Controls (RBAC) and MFA?",
        guidance="Review permissions to verify that only authorized personnel can access sensitive customer contact details, vehicle service histories, or appointment logs.",
        why_it_matters="Permissive internal access and shared terminal logins are leading root causes of customer data leaks and insider threats."
    ),
    QuestionDefinition(
        id="P3",
        category="privacy",
        category_title="Data Privacy & Governance",
        question_text="Is there a defined, automated data retention and disposal schedule for datasets collected and processed by this AI system?",
        guidance="Determine whether temporary customer chat inquiries, vehicle assessment photos, and legacy booking records are securely purged or anonymized after a defined legal holding period (e.g. 12 months).",
        why_it_matters="Indefinite data hoarding violates privacy laws and creates compounding litigation and cyber liability."
    ),
    QuestionDefinition(
        id="P4",
        category="privacy",
        category_title="Data Privacy & Governance",
        question_text="Are all sensitive data fields encrypted both in transit (TLS 1.3) and at rest (AES-256) throughout the entire AI pipeline?",
        guidance="Verify cryptographic protection on database volumes, customer communications, cloud storage buckets, and intermediate caching layers.",
        why_it_matters="Unencrypted customer booking batches and cache files expose the organization to immediate regulatory fines upon breach."
    ),
    QuestionDefinition(
        id="P5",
        category="privacy",
        category_title="Data Privacy & Governance",
        question_text="Does the organization maintain documented data governance procedures, privacy impact assessments (PIA), and vendor third-party vetting for AI tools?",
        guidance="Assess whether third-party conversational AI APIs, cloud hosts, and messaging sub-processors undergo written data protection and confidentiality reviews.",
        why_it_matters="SMEs are legally accountable for third-party sub-processors; using unvetted AI APIs can leak proprietary and customer data."
    ),

    # SUSTAINABILITY
    QuestionDefinition(
        id="S1",
        category="sustainability",
        category_title="Green AI & Sustainability",
        question_text="Does your team track compute duration, GPU/CPU utilization, and estimated energy consumption for model training and batch inference runs?",
        guidance="Check if runtime telemetry or cloud billing compute-hour metrics are monitored for hosting the detailing assistant and recommendation endpoints.",
        why_it_matters="You cannot reduce carbon impact or optimize runaway cloud compute costs without measuring baseline energy consumption."
    ),
    QuestionDefinition(
        id="S2",
        category="sustainability",
        category_title="Green AI & Sustainability",
        question_text="Are AI computing resources optimized (e.g. right-sizing cloud instances, auto-scaling to zero when idle, leveraging spot instances)?",
        guidance="Verify if customer inquiry servers scale down during non-business hours or dynamically match online appointment booking traffic.",
        why_it_matters="Idle GPU/cloud instances outside shop operating hours generate unnecessary carbon emissions and drain SME operating capital."
    ),
    QuestionDefinition(
        id="S3",
        category="sustainability",
        category_title="Green AI & Sustainability",
        question_text="Does the system avoid unnecessary redundant processing by caching inference results and executing batched evaluations where applicable?",
        guidance="Confirm whether repetitive identical queries (e.g., standard detailing package recommendations for common car models) hit a low-latency cache rather than re-running deep model inference.",
        why_it_matters="Redundant re-computation wastes electric power and multiplies API token/inference expenses."
    ),
    QuestionDefinition(
        id="S4",
        category="sustainability",
        category_title="Green AI & Sustainability",
        question_text="Have your engineers evaluated lightweight, energy-efficient model architectures (e.g. distilled models, quantization, classical ML) before choosing heavy foundation models?",
        guidance="Assess whether compact models (e.g. LightGBM, quantized small models) were benchmarked against massive multi-billion parameter networks for routine package matching and slot scheduling.",
        why_it_matters="Using massive LLMs or oversized transformers for routine booking or classification tasks consumes 100x more energy for negligible accuracy gain."
    ),
    QuestionDefinition(
        id="S5",
        category="sustainability",
        category_title="Green AI & Sustainability",
        question_text="Does the organization evaluate the regional carbon intensity and renewable energy factor of the cloud data centers hosting its AI workloads?",
        guidance="Determine if cloud workloads are hosted in data centers with low carbon grid factors (e.g., regions powered by hydro/solar/nuclear).",
        why_it_matters="Hosting customer-facing AI workloads in a clean grid region can cut actual operational greenhouse gas emissions by up to 70%."
    )
]

def get_questions(
    business: Optional[Business] = None,
    application: Optional[AIApplication] = None,
    force_llm: bool = False
) -> List[QuestionDefinition]:
    if business and application:
        return generate_industry_assessment(business, application, force_llm=force_llm)
    return QUESTIONS_CATALOG

def score_assessment(
    responses: List[Dict[str, Any]],
    question_catalog: Optional[List[QuestionDefinition]] = None
) -> Tuple[Dict[str, float], float, Dict[str, Dict[str, Any]]]:
    """
    Scoring Rule:
    - Yes = 100
    - Partially = 50
    - No = 0
    - N/A excluded from calculation
    - Dimension score = sum(scores) / count(valid responses)
    - Overall score = mean of the 4 dimension scores
    """
    category_scores = {
        "fairness": [],
        "transparency": [],
        "privacy": [],
        "sustainability": []
    }
    
    catalog = question_catalog or QUESTIONS_CATALOG
    response_details = {}

    for resp in responses:
        q_id = resp.get("question_id")
        ans = resp.get("answer", "No")
        notes = resp.get("notes", "")

        score = None
        if ans == "Yes":
            score = 100.0
        elif ans == "Partially":
            score = 50.0
        elif ans == "No":
            score = 0.0
        elif ans == "N/A":
            score = None

        # Find matching question in dynamic or fallback catalog
        q_def = next((q for q in catalog if q.id == q_id), None)
        category = q_def.category if q_def else resp.get("category", "fairness")
        q_text = q_def.question_text if q_def else resp.get("question_text", f"Question {q_id}")
        guidance = q_def.guidance if q_def else resp.get("guidance", "")
        evidence_req = q_def.evidence_required if q_def else resp.get("evidence_required", "")
        risk_sev = q_def.risk_severity if q_def else resp.get("risk_severity", "High")
        rec_text = q_def.recommendation if q_def else resp.get("recommendation_text", "")
        risk_cat = q_def.risk_category if q_def else resp.get("risk_category", f"{category.title()} Risk")
        why_it_matters = q_def.why_it_matters if q_def else "Creates governance exposure."

        if score is not None:
            if category in category_scores:
                category_scores[category].append(score)
            else:
                category_scores["fairness"].append(score)
            
        response_details[q_id] = {
            "question_id": q_id,
            "category": category,
            "question_text": q_text,
            "guidance": guidance,
            "evidence_required": evidence_req,
            "risk_severity": risk_sev,
            "recommendation_text": rec_text,
            "risk_category": risk_cat,
            "why_it_matters": why_it_matters,
            "answer": ans,
            "score": score,
            "notes": notes
        }

    dimension_results = {}
    for cat in ["fairness", "transparency", "privacy", "sustainability"]:
        scores = category_scores[cat]
        if scores:
            dimension_results[cat] = round(sum(scores) / len(scores), 1)
        else:
            dimension_results[cat] = 0.0

    overall = round(sum(dimension_results.values()) / 4.0, 1)
    return dimension_results, overall, response_details

def process_and_save_assessment(
    db: Session,
    data: AssessmentCreate,
    user_id: Optional[int] = None
) -> Assessment:
    # 1. Resolve application and business
    app_obj = db.query(AIApplication).filter(AIApplication.id == data.application_id).first()
    biz_obj = None
    if data.business_id:
        biz_obj = db.query(Business).filter(Business.id == data.business_id).first()
    elif app_obj and app_obj.business_id:
        biz_obj = db.query(Business).filter(Business.id == app_obj.business_id).first()

    # Generate or retrieve dynamic question catalog for this application
    if biz_obj and app_obj:
        q_defs = generate_industry_assessment(biz_obj, app_obj)
    else:
        q_defs = QUESTIONS_CATALOG

    # 2. Mark previous assessments for this application as is_current = False
    db.query(Assessment).filter(
        Assessment.application_id == data.application_id
    ).update({"is_current": False})
    db.commit()

    # 3. Calculate scores with dynamic question catalog
    raw_responses = [
        {
            "question_id": r.question_id,
            "answer": r.answer,
            "notes": r.notes,
            "guidance": getattr(r, "guidance", None),
            "evidence_required": getattr(r, "evidence_required", None),
            "risk_severity": getattr(r, "risk_severity", None),
            "recommendation_text": getattr(r, "recommendation_text", None)
        }
        for r in data.responses
    ]
    dim_scores, overall, details = score_assessment(raw_responses, question_catalog=q_defs)

    industry_name = biz_obj.industry if biz_obj and biz_obj.industry else (app_obj.business_function or "General SME")

    # 4. Create Assessment with multi-business isolation & dynamic snapshot
    assessment = Assessment(
        business_id=data.business_id or (biz_obj.id if biz_obj else 1),
        application_id=data.application_id,
        user_id=user_id,
        name=data.name,
        industry=industry_name,
        question_version="2.0",
        question_set_json=json.dumps([q.dict() for q in q_defs]),
        overall_score=overall,
        fairness_score=dim_scores["fairness"],
        transparency_score=dim_scores["transparency"],
        privacy_score=dim_scores["privacy"],
        sustainability_score=dim_scores["sustainability"],
        notes=data.notes,
        is_current=True
    )
    db.add(assessment)
    db.flush()

    # 5. Save individual responses and generate actionable domain risks & recommendations
    for q_id, d in details.items():
        resp_obj = AssessmentResponse(
            assessment_id=assessment.id,
            question_id=q_id,
            category=d["category"],
            question_text=d["question_text"],
            guidance=d.get("guidance"),
            evidence_required=d.get("evidence_required"),
            risk_severity=d.get("risk_severity"),
            recommendation_text=d.get("recommendation_text"),
            answer=d["answer"],
            score=d["score"],
            notes=d["notes"]
        )
        db.add(resp_obj)

    db.commit()

    # 6. Centralized Universal Risk Intelligence Engine
    # Evaluates risks, computes multi-factor scores, prevents duplicates, tracks lifecycle, and synchronizes recommendations
    RiskIntelligenceEngine.evaluate_and_sync(
        db=db,
        application_id=data.application_id,
        assessment_id=assessment.id,
        responses=raw_responses,
        actor_email=f"user_{user_id}" if user_id else "system_assessment"
    )

    db.refresh(assessment)
    return assessment
