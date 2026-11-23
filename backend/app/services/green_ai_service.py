import json
from typing import Dict, Any, List, Optional
from ..models import SustainabilityResult, Risk
from sqlalchemy.orm import Session

# Standard Grid Emission Factors (kg CO2e per kWh) based on EPA, EEA, CEA baselines
REGION_EMISSION_FACTORS: Dict[str, Dict[str, Any]] = {
    "us-east-grid": {
        "name": "US East (PJM / RFC Grid)",
        "factor": 0.385,
        "description": "Standard US commercial grid mix (natural gas & nuclear predominant)"
    },
    "us-west-clean": {
        "name": "US West (Clean Hydro / Solar)",
        "factor": 0.190,
        "description": "High renewable proportion (hydro, wind, solar)"
    },
    "eu-average": {
        "name": "EU European Average Grid",
        "factor": 0.230,
        "description": "European Union cross-border grid average (nuclear & wind prevalent)"
    },
    "india-cea": {
        "name": "India National Grid (CEA)",
        "factor": 0.710,
        "description": "Thermal coal intensive grid baseline"
    },
    "cloud-datacenter-green": {
        "name": "Green Cloud Facility (PUE 1.1 + Renewable PPA)",
        "factor": 0.050,
        "description": "Modern hyperscale datacenter with matched clean energy PPAs"
    },
    "global-average": {
        "name": "Global Baseline Grid Mix",
        "factor": 0.475,
        "description": "Worldwide average grid emission intensity"
    }
}

def calculate_sustainability_metrics(
    runtime_hours: float,
    power_kw: Optional[float] = None,
    power_draw_kw: Optional[float] = None,
    emission_factor_override: Optional[float] = None,
    region_preset: Optional[str] = "us-east-grid"
) -> Dict[str, Any]:
    """
    Computes precise electrical energy and carbon footprint:
    Energy (kWh) = Power (kW) x Runtime (hours)
    Estimated CO2e (kg) = Energy (kWh) x Emission Factor (kg CO2e/kWh)
    """
    if power_kw is None and power_draw_kw is not None:
        power_kw = power_draw_kw
    elif power_kw is None:
        power_kw = 0.0
    if runtime_hours < 0:
        runtime_hours = 0.0
    if power_kw < 0:
        power_kw = 0.0

    region_meta = REGION_EMISSION_FACTORS.get(region_preset, REGION_EMISSION_FACTORS["global-average"])
    
    if emission_factor_override is not None and emission_factor_override > 0:
        emission_factor = emission_factor_override
        region_label = f"Custom Factor ({emission_factor:.3f} kg CO2e/kWh)"
    else:
        emission_factor = region_meta["factor"]
        region_label = region_meta["name"]

    # Core Calculations
    energy_kwh = round(power_kw * runtime_hours, 3)
    estimated_co2e_kg = round(energy_kwh * emission_factor, 3)

    # Equivalencies for intuitive SME executive context
    # 1 mile driven by average gasoline passenger car ≈ 0.392 kg CO2e (EPA estimate)
    # 1 urban tree seedling grown for 10 years sequesters ≈ 60 kg CO2 (EPA estimate)
    equivalent_car_miles = round(estimated_co2e_kg / 0.392, 1) if estimated_co2e_kg > 0 else 0.0
    tree_seedlings = round(estimated_co2e_kg / 60.0, 2) if estimated_co2e_kg > 0 else 0.0

    # Optimization Scenarios (quantifying tangible business and ESG benefits)
    # Average commercial electricity tariff: ~$0.14 / kWh
    kwh_cost_usd = 0.14

    scenarios = [
        {
            "scenario_name": "Model Quantization (FP32 -> INT8/FP16)",
            "description": "Compressing weights cuts memory bus transfers and GPU compute time by ~40-45%.",
            "projected_energy_kwh": round(energy_kwh * 0.55, 3),
            "projected_co2e_kg": round(estimated_co2e_kg * 0.55, 3),
            "reduction_percentage": 45.0,
            "annual_cost_savings_estimate_usd": round((energy_kwh * 0.45 * kwh_cost_usd) * 12, 2)
        },
        {
            "scenario_name": "Dynamic Idle Scaling & Workload Batching",
            "description": "Scale cloud inference instances to zero when inactive and batch periodic scoring jobs.",
            "projected_energy_kwh": round(energy_kwh * 0.65, 3),
            "projected_co2e_kg": round(estimated_co2e_kg * 0.65, 3),
            "reduction_percentage": 35.0,
            "annual_cost_savings_estimate_usd": round((energy_kwh * 0.35 * kwh_cost_usd) * 12, 2)
        },
        {
            "scenario_name": "Green Datacenter Relocation",
            "description": "Migrate cloud workloads to a renewable-matched region (0.050 kg CO2e/kWh).",
            "projected_energy_kwh": energy_kwh,
            "projected_co2e_kg": round(energy_kwh * 0.050, 3),
            "reduction_percentage": round((1.0 - (0.050 / emission_factor)) * 100, 1) if emission_factor > 0.050 else 0.0,
            "annual_cost_savings_estimate_usd": 0.0  # primary benefit is carbon reduction
        },
        {
            "scenario_name": "Lightweight Architecture Distillation",
            "description": "Replace redundant deep transformers with fine-tuned tree or distilled models for tabular scoring.",
            "projected_energy_kwh": round(energy_kwh * 0.40, 3),
            "projected_co2e_kg": round(estimated_co2e_kg * 0.40, 3),
            "reduction_percentage": 60.0,
            "annual_cost_savings_estimate_usd": round((energy_kwh * 0.60 * kwh_cost_usd) * 12, 2)
        }
    ]

    actionable_recommendations = [
        "Enable GPU auto-sleep or serverless CPU inference for low-concurrency SME business hours.",
        "Implement model quantization (INT8) to halve memory footprint and cut per-inference energy by 45%.",
        "Set cloud deployment region to low-carbon zones (e.g., us-west1 or europe-north1) to slash net CO2e.",
        "Cache frequent or duplicate candidate scoring inferences to eliminate zero-value recomputations."
    ]

    assumptions_disclaimer = (
        "ENERGY ESTIMATION ASSUMPTIONS: Calculations represent statistical energy modeling based on specified power rating, "
        "runtime duration, and regional grid emission factors. This does NOT claim direct physical power meter hardware telemetry."
    )

    return {
        "compute_duration_hours": runtime_hours,
        "power_draw_kw": power_kw,
        "energy_kwh": energy_kwh,
        "emission_factor_kg_per_kwh": emission_factor,
        "region_name": region_label,
        "estimated_co2e_kg": estimated_co2e_kg,
        "equivalent_car_miles": equivalent_car_miles,
        "tree_seedlings_needed_10_years": tree_seedlings,
        "scenarios": scenarios,
        "actionable_recommendations": actionable_recommendations,
        "assumptions_disclaimer": assumptions_disclaimer
    }

def record_sustainability_findings(
    db: Session,
    application_id: int,
    results: Dict[str, Any],
    assessment_id: Optional[int] = None
) -> SustainabilityResult:
    s_res = SustainabilityResult(
        application_id=application_id,
        assessment_id=assessment_id,
        compute_duration_hours=results["compute_duration_hours"],
        power_draw_kw=results["power_draw_kw"],
        energy_kwh=results["energy_kwh"],
        emission_factor=results["emission_factor_kg_per_kwh"],
        estimated_co2e_kg=results["estimated_co2e_kg"],
        region_name=results["region_name"],
        optimization_scenarios_json=json.dumps(results["scenarios"])
    )
    db.add(s_res)

    # If carbon footprint is abnormally high (> 500 kg CO2e) or energy is unmonitored, add Risk
    if results["estimated_co2e_kg"] > 500:
        risk = Risk(
            application_id=application_id,
            assessment_id=assessment_id,
            title="Elevated Environmental Footprint in Continuous AI Inference",
            description=f"Model execution generates an estimated {results['estimated_co2e_kg']:.1f} kg CO2e per cycle ({results['energy_kwh']:.1f} kWh).",
            source_module="sustainability",
            severity="Medium",
            evidence=f"Estimated carbon footprint of {results['estimated_co2e_kg']} kg CO2e over {results['compute_duration_hours']} hours at {results['power_draw_kw']} kW.",
            business_impact="Rising ESG disclosure penalties, compliance scrutiny under CSRD/Scope 3 directives, and escalating cloud hosting overhead.",
            recommended_action="Adopt model quantization and migrate workloads to high-efficiency clean-energy cloud zones.",
            status="Open"
        )
        db.add(risk)

    db.commit()
    db.refresh(s_res)
    return s_res
