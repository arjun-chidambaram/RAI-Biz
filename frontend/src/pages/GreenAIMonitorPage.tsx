import React, { useState, useEffect } from 'react';
import {
  Leaf,
  Zap,
  TrendingDown,
  DollarSign,
  Car,
  Trees,
  Info,
  CheckCircle2,
  HelpCircle,
  Cpu,
  Globe,
  ArrowRight
} from 'lucide-react';
import { api, SustainabilityResponse } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const GreenAIMonitorPage: React.FC = () => {
  const { application } = useAuth();
  const [runtimeHours, setRuntimeHours] = useState<number>(240);
  const [powerKw, setPowerKw] = useState<number>(0.85);
  const [regionPreset, setRegionPreset] = useState<string>('us-east-grid');
  const [customFactor, setCustomFactor] = useState<string>('');
  const [calculating, setCalculating] = useState(false);
  const [results, setResults] = useState<SustainabilityResponse | null>(null);

  useEffect(() => {
    recalculate();
  }, [runtimeHours, powerKw, regionPreset, customFactor]);

  const recalculate = async () => {
    try {
      setCalculating(true);
      const res = await api.calculateSustainability({
        application_id: application?.id || 1,
        compute_duration_hours: Number(runtimeHours),
        power_draw_kw: Number(powerKw),
        emission_factor_kg_per_kwh: customFactor ? Number(customFactor) : undefined,
        region_preset: customFactor ? undefined : regionPreset
      });
      setResults(res);
    } catch (err) {
      console.error(err);
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200">
                MODULE 5
              </span>
              <span className="text-xs text-slate-400 font-medium">Energy Modeling • Scope 2/3 GHG Accounting</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">Green AI & Carbon Footprint Monitor</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Calculate electrical energy usage (kWh) and greenhouse gas emissions (kg CO2e) from AI training and continuous batch inference workloads.
            </p>
          </div>

          <div className="flex items-center space-x-2 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl text-emerald-800 text-xs font-semibold">
            <Leaf className="w-4 h-4 text-emerald-600" />
            <span>ESG & Cost Optimization</span>
          </div>
        </div>

        {/* Interactive Parameter Controls */}
        <div className="mt-6 pt-5 border-t border-slate-100 grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          {/* Runtime Hours */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex justify-between items-center mb-1">
              <label className="font-semibold text-slate-700">Compute Duration</label>
              <span className="font-bold text-teal-700">{runtimeHours} hrs</span>
            </div>
            <input
              type="range"
              min="1"
              max="1000"
              step="5"
              value={runtimeHours}
              onChange={(e) => setRuntimeHours(Number(e.target.value))}
              className="w-full accent-teal-600 cursor-pointer"
            />
            <span className="text-[10px] text-slate-400 block mt-1">Monthly inference/training runtime</span>
          </div>

          {/* Power Draw kW */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex justify-between items-center mb-1">
              <label className="font-semibold text-slate-700">Server Power Draw</label>
              <span className="font-bold text-teal-700">{powerKw} kW</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="10.0"
              step="0.05"
              value={powerKw}
              onChange={(e) => setPowerKw(Number(e.target.value))}
              className="w-full accent-teal-600 cursor-pointer"
            />
            <span className="text-[10px] text-slate-400 block mt-1">e.g. 1 GPU Server ≈ 0.4 - 1.2 kW</span>
          </div>

          {/* Grid Region Preset */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <label className="font-semibold text-slate-700 block mb-1">Grid Carbon Intensity</label>
            <select
              value={regionPreset}
              disabled={!!customFactor}
              onChange={(e) => setRegionPreset(e.target.value)}
              className="w-full text-xs px-2 py-1.5 rounded-lg bg-white border border-slate-200 focus:outline-hidden"
            >
              <option value="us-east-grid">US East (0.385 kg/kWh)</option>
              <option value="us-west-clean">US West Clean (0.190 kg/kWh)</option>
              <option value="eu-average">EU European Average (0.230 kg/kWh)</option>
              <option value="india-cea">India CEA Grid (0.710 kg/kWh)</option>
              <option value="cloud-datacenter-green">Hyperscale Green (0.050 kg/kWh)</option>
              <option value="global-average">Global Mix (0.475 kg/kWh)</option>
            </select>
            <span className="text-[10px] text-slate-400 block mt-1">Official EPA / EEA grid factor</span>
          </div>

          {/* Custom Factor Override */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <label className="font-semibold text-slate-700 block mb-1">Custom Factor (Optional)</label>
            <input
              type="number"
              placeholder="e.g. 0.35"
              step="0.01"
              value={customFactor}
              onChange={(e) => setCustomFactor(e.target.value)}
              className="w-full text-xs px-2 py-1.5 rounded-lg bg-white border border-slate-200 focus:outline-hidden"
            />
            <span className="text-[10px] text-slate-400 block mt-1">Overrides preset if entered</span>
          </div>
        </div>
      </div>

      {results && (
        <>
          {/* Main Calculation KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Total Energy kWh */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 block">Electrical Energy</span>
                <span className="text-2xl font-extrabold text-slate-900 mt-1 block">
                  {results.energy_kwh.toFixed(1)} kWh
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">Energy = Power (kW) × Runtime (h)</p>
              </div>
              <div className="mt-4 flex items-center space-x-1.5 text-xs text-teal-700 font-semibold">
                <Zap className="w-4 h-4 text-teal-600" />
                <span>Est. Electricity: ~${(results.energy_kwh * 0.14).toFixed(2)}</span>
              </div>
            </div>

            {/* Estimated CO2e kg */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 block">Carbon Footprint</span>
                <span className={`text-2xl font-extrabold mt-1 block ${results.estimated_co2e_kg > 100 ? 'text-amber-600' : 'text-emerald-600'}`}>
                  {results.estimated_co2e_kg.toFixed(1)} kg CO2e
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">Energy (kWh) × Factor ({results.emission_factor_kg_per_kwh})</p>
              </div>
              <div className="mt-4 text-xs font-semibold text-slate-600">
                Region: {results.region_name.split('(')[0]}
              </div>
            </div>

            {/* Passenger Car Equivalent */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 block">Gasoline Car Miles Driven</span>
                <span className="text-2xl font-extrabold text-slate-900 mt-1 block">
                  {results.equivalent_car_miles.toFixed(0)} miles
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">EPA average passenger vehicle equivalence</p>
              </div>
              <div className="mt-4 flex items-center space-x-1 text-xs text-slate-500">
                <Car className="w-4 h-4 text-slate-400" />
                <span>~0.39 kg CO2e / mile</span>
              </div>
            </div>

            {/* Tree Seedlings Needed */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 block">Tree Seedlings (10 yrs)</span>
                <span className="text-2xl font-extrabold text-slate-900 mt-1 block">
                  {results.tree_seedlings_needed_10_years.toFixed(1)} trees
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">Required to sequester emitted carbon</p>
              </div>
              <div className="mt-4 flex items-center space-x-1 text-xs text-emerald-700 font-semibold">
                <Trees className="w-4 h-4 text-emerald-600" />
                <span>60 kg CO2 / tree</span>
              </div>
            </div>
          </div>

          {/* Optimization Scenarios Grid */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Carbon & Cloud Cost Optimization Scenarios</h2>
                <p className="text-xs text-slate-500">Projected savings from software engineering and cloud architectural adjustments</p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-md bg-teal-50 text-teal-700 font-bold border border-teal-200">
                4 Scenarios Evaluated
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {results.scenarios.map((sc, i) => (
                <div key={i} className="p-4 rounded-xl border border-slate-200/80 hover:border-teal-300 transition bg-slate-50/50 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-bold text-slate-900 leading-tight">
                        {sc.scenario_name}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-100 text-emerald-800">
                        -{sc.reduction_percentage.toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      {sc.description}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-200/60 text-xs space-y-1">
                    <div className="flex justify-between text-slate-600 text-[11px]">
                      <span>Projected Energy:</span>
                      <b>{sc.projected_energy_kwh.toFixed(1)} kWh</b>
                    </div>
                    <div className="flex justify-between text-emerald-700 font-bold text-[11px]">
                      <span>Projected CO2e:</span>
                      <b>{sc.projected_co2e_kg.toFixed(1)} kg</b>
                    </div>
                    {sc.annual_cost_savings_estimate_usd > 0 && (
                      <div className="flex justify-between text-teal-800 font-bold text-[11px] pt-1">
                        <span>Annual Savings:</span>
                        <b>~${sc.annual_cost_savings_estimate_usd.toFixed(0)} / yr</b>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Actionable Engineering Recommendations */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
            <h2 className="text-sm font-bold text-slate-900 mb-3 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-teal-600" />
              <span>SME Green AI Best Practices</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-600">
              {results.actionable_recommendations.map((rec, i) => (
                <div key={i} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-start space-x-2">
                  <span className="w-4 h-4 rounded-full bg-teal-100 text-teal-800 font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Modeling Assumptions Disclaimer */}
          <div className="p-4 rounded-xl bg-slate-100/80 border border-slate-200 text-slate-500 text-[11px] leading-relaxed flex items-start space-x-3">
            <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
            <div>
              <b>Statistical Modeling Caveat:</b> {results.assumptions_disclaimer}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
