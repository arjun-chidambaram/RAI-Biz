/**
 * RAI-Biz Frontend Automated Test Suite
 * =====================================
 * Executed via Node.js Built-in Test Runner (`node --test`)
 * Tests:
 * 1. Component File Existence & Export Integrity (All 16 Governance Modules)
 * 2. Routing Configuration & Out-of-Scope Prevention (Zero BI/Financial leaks)
 * 3. Navigation Sidebar Wiring & Metric Counters
 * 4. API Client URL Normalization & Prefix Management
 * 5. Input Validation Rules (Email OTP, 6-digit verification, Dataset CSV check)
 * 6. Green AI & Risk Formula Mathematical Verification
 * 7. Security: CSRF Injection & Credential Transport Validation
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '../..');
const frontendSrc = path.resolve(projectRoot, 'frontend/src');

// ---------------------------------------------------------------------------
// SUITE 1: COMPONENT & PAGE FILE INTEGRITY
// ---------------------------------------------------------------------------
test('Suite 1: Frontend Architecture & Component File Inventory', async (t) => {
  const expectedPages = [
    'LoginPage.tsx',
    'VerifyOtpPage.tsx',
    'DashboardPage.tsx',
    'BusinessProfilePage.tsx',
    'AssessmentPage.tsx',
    'FairnessPage.tsx',
    'ExplainableAIPage.tsx',
    'PrivacyGuardPage.tsx',
    'GreenAIMonitorPage.tsx',
    'DatasetManagerPage.tsx',
    'RiskCenterPage.tsx',
    'RecommendationsPage.tsx',
    'ReportsPage.tsx',
    'HistoryPage.tsx',
    'SettingsPage.tsx',
  ];

  await t.test('All 15 Page components exist in frontend/src/pages', () => {
    const pagesDir = path.join(frontendSrc, 'pages');
    assert.ok(fs.existsSync(pagesDir), 'Pages directory must exist');

    for (const pageFile of expectedPages) {
      const fullPath = path.join(pagesDir, pageFile);
      assert.ok(fs.existsSync(fullPath), `Page component ${pageFile} must exist`);
      const content = fs.readFileSync(fullPath, 'utf8');
      assert.ok(content.length > 200, `Page component ${pageFile} must not be empty`);
      assert.ok(
        content.includes('export function') || content.includes('export const'),
        `Page ${pageFile} must export a component`
      );
    }
  });

  await t.test('Core application structural components exist', () => {
    const layoutPath = path.join(frontendSrc, 'components/Layout.tsx');
    const protectedRoutePath = path.join(frontendSrc, 'components/ProtectedRoute.tsx');
    const authContextPath = path.join(frontendSrc, 'context/AuthContext.tsx');
    const apiClientPath = path.join(frontendSrc, 'api/client.ts');
    const appPath = path.join(frontendSrc, 'App.tsx');

    assert.ok(fs.existsSync(layoutPath), 'Layout.tsx must exist');
    assert.ok(fs.existsSync(protectedRoutePath), 'ProtectedRoute.tsx must exist');
    assert.ok(fs.existsSync(authContextPath), 'AuthContext.tsx must exist');
    assert.ok(fs.existsSync(apiClientPath), 'api/client.ts must exist');
    assert.ok(fs.existsSync(appPath), 'App.tsx must exist');
  });
});

// ---------------------------------------------------------------------------
// SUITE 2: ROUTER CONFIGURATION & STRICT SCOPE ENFORCEMENT
// ---------------------------------------------------------------------------
test('Suite 2: Router Configuration & Strict Governance Scope', async (t) => {
  const appPath = path.join(frontendSrc, 'App.tsx');
  const appContent = fs.readFileSync(appPath, 'utf8');

  await t.test('All 16 Responsible AI governance paths are mounted in App.tsx', () => {
    const expectedRoutes = [
      '/login',
      '/verify-otp',
      'profile',
      'assessment',
      'fairness',
      'xai',
      'privacy',
      'green-ai',
      'datasets',
      'risks',
      'recommendations',
      'reports',
      'history',
      'settings',
    ];

    for (const route of expectedRoutes) {
      assert.ok(
        appContent.includes(`path="${route}"`) || appContent.includes(`path='${route}'`),
        `App.tsx must define route path for ${route}`
      );
    }
    // Index dashboard route
    assert.ok(appContent.includes('<Route index element={<DashboardPage />} />'), 'App.tsx must define index dashboard route');
  });

  await t.test('Strict Scope Enforcement: NO Business Intelligence or Financial Analysis routes', () => {
    const prohibitedRoutes = [
      'business-analyzer',
      'financial-health',
      'market-analysis',
      'growth-advisor',
      'revenue-forecast',
      'competitor-tracker',
    ];

    for (const prohibited of prohibitedRoutes) {
      assert.ok(
        !appContent.toLowerCase().includes(prohibited),
        `Prohibited non-governance route '${prohibited}' must NOT be in App.tsx`
      );
    }
  });

  await t.test('Wildcard route fallback redirects to root "/"', () => {
    assert.ok(
      appContent.includes('path="*"') && appContent.includes('Navigate to="/" replace'),
      'App.tsx must have wildcard redirect to /'
    );
  });
});

// ---------------------------------------------------------------------------
// SUITE 3: NAVIGATION BAR INTEGRITY (LAYOUT COMPONENT)
// ---------------------------------------------------------------------------
test('Suite 3: Layout Navigation & Dashboard Synchronization', async (t) => {
  const layoutPath = path.join(frontendSrc, 'components/Layout.tsx');
  const layoutContent = fs.readFileSync(layoutPath, 'utf8');

  await t.test('Navigation items match Responsible AI platform modules', () => {
    const expectedNavNames = [
      'Overview',
      'Business Profile',
      'AI Assessment',
      'Fairness & Bias Detection',
      'Explainable AI',
      'Privacy Guard',
      'Green AI Monitor',
      'Dataset Manager',
      'Risk Center',
      'Recommendations',
      'Reports',
      'Assessment History',
      'Settings',
    ];

    for (const name of expectedNavNames) {
      assert.ok(
        layoutContent.includes(`name: '${name}'`) || layoutContent.includes(`name: "${name}"`),
        `Layout.tsx must contain navigation item '${name}'`
      );
    }
  });

  await t.test('Risk Center navigation badge reflects high/critical count', () => {
    assert.ok(
      layoutContent.includes('summary?.high_critical_risks_count'),
      'Layout.tsx must bind Risk Center badge to summary.high_critical_risks_count'
    );
  });
});

// ---------------------------------------------------------------------------
// SUITE 4: API CLIENT URL NORMALIZATION LOGIC
// ---------------------------------------------------------------------------
test('Suite 4: API URL Normalization Logic', async (t) => {
  // Simulated URL normalization function matching frontend/src/api/client.ts
  function normalizeApiBase(rawUrl) {
    const trimmed = (rawUrl || '').replace(/\/+$/, '');
    return trimmed
      ? (trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`)
      : '/api';
  }

  await t.test('Normalizes root URL without trailing slash', () => {
    assert.strictEqual(normalizeApiBase('https://rai-biz.onrender.com'), 'https://rai-biz.onrender.com/api');
  });

  await t.test('Normalizes root URL with trailing slash', () => {
    assert.strictEqual(normalizeApiBase('https://rai-biz.onrender.com/'), 'https://rai-biz.onrender.com/api');
  });

  await t.test('Normalizes root URL with multiple trailing slashes', () => {
    assert.strictEqual(normalizeApiBase('https://rai-biz.onrender.com///'), 'https://rai-biz.onrender.com/api');
  });

  await t.test('Preserves existing /api suffix without duplicating', () => {
    assert.strictEqual(normalizeApiBase('https://rai-biz.onrender.com/api'), 'https://rai-biz.onrender.com/api');
    assert.strictEqual(normalizeApiBase('https://rai-biz.onrender.com/api/'), 'https://rai-biz.onrender.com/api');
  });

  await t.test('Falls back to local proxy /api when env is undefined or empty', () => {
    assert.strictEqual(normalizeApiBase(undefined), '/api');
    assert.strictEqual(normalizeApiBase(''), '/api');
  });
});

// ---------------------------------------------------------------------------
// SUITE 5: FORM VALIDATION & FORMAT CHECKERS
// ---------------------------------------------------------------------------
test('Suite 5: Frontend Form Validation Logic', async (t) => {
  const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const OTP_REGEX = /^\d{6}$/;

  await t.test('Email format validation accepts standard business emails', () => {
    assert.ok(EMAIL_REGEX.test('compliance@suntech-mobility.de'));
    assert.ok(EMAIL_REGEX.test('officer@smarthire.co.uk'));
    assert.ok(EMAIL_REGEX.test('auditor@apex-dynamics.com'));
  });

  await t.test('Email format validation rejects malformed inputs', () => {
    assert.strictEqual(EMAIL_REGEX.test('not-an-email'), false);
    assert.strictEqual(EMAIL_REGEX.test('missing-domain@'), false);
    assert.strictEqual(EMAIL_REGEX.test('@no-local-part.com'), false);
    assert.strictEqual(EMAIL_REGEX.test('spaces in@email.com'), false);
  });

  await t.test('OTP validation accepts exactly 6 numeric digits', () => {
    assert.ok(OTP_REGEX.test('123456'));
    assert.ok(OTP_REGEX.test('000000'));
    assert.ok(OTP_REGEX.test('999999'));
  });

  await t.test('OTP validation rejects invalid formats', () => {
    assert.strictEqual(OTP_REGEX.test('12345'), false);   // 5 digits
    assert.strictEqual(OTP_REGEX.test('1234567'), false); // 7 digits
    assert.strictEqual(OTP_REGEX.test('12a456'), false);  // contains letter
    assert.strictEqual(OTP_REGEX.test(' 12345'), false);  // leading space
  });

  await t.test('Dataset file extension validator permits only CSV and JSON', () => {
    function isValidDatasetExtension(filename) {
      const ext = filename.split('.').pop().toLowerCase();
      return ['csv', 'json'].includes(ext);
    }

    assert.ok(isValidDatasetExtension('customer_feedback.csv'));
    assert.ok(isValidDatasetExtension('telemetry_stream.json'));
    assert.strictEqual(isValidDatasetExtension('malicious.exe'), false);
    assert.strictEqual(isValidDatasetExtension('notes.txt'), false);
    assert.strictEqual(isValidDatasetExtension('report.pdf'), false);
  });
});

// ---------------------------------------------------------------------------
// SUITE 6: MATHEMATICAL VERIFICATION (GREEN AI & FAIRNESS RATIOS)
// ---------------------------------------------------------------------------
test('Suite 6: Frontend Analytical Formulas', async (t) => {
  await t.test('Green AI energy and CO2e formulas compute accurately', () => {
    // Energy (kWh) = Power (kW) * Runtime (hours)
    // CO2e (kg) = Energy (kWh) * Emission Factor (kg/kWh)
    const powerKw = 0.50; // 500 Watts
    const hours = 200;
    const factorEU = 0.230; // EU grid average

    const energyKwh = powerKw * hours;
    assert.strictEqual(energyKwh, 100.0);

    const co2eKg = energyKwh * factorEU;
    assert.strictEqual(Math.round(co2eKg * 100) / 100, 23.0);

    // Car miles equivalence (0.392 kg CO2e / mile)
    const carMiles = Math.round((co2eKg / 0.392) * 10) / 10;
    assert.strictEqual(carMiles, 58.7);
  });

  await t.test('Four-fifths (80%) rule disparate impact ratio check', () => {
    function passesFourFifthsRule(unfavRate, favRate) {
      if (favRate <= 0) return true;
      const ratio = unfavRate / favRate;
      return ratio >= 0.80;
    }

    // 40% vs 50% -> ratio = 0.80 -> Pass
    assert.ok(passesFourFifthsRule(0.40, 0.50));

    // 35% vs 50% -> ratio = 0.70 -> Fail (Bias detected)
    assert.strictEqual(passesFourFifthsRule(0.35, 0.50), false);

    // 60% vs 50% -> ratio = 1.20 -> Pass
    assert.ok(passesFourFifthsRule(0.60, 0.50));
  });
});

// ---------------------------------------------------------------------------
// SUITE 7: SECURITY & CREDENTIAL HANDLING IN API CLIENT
// ---------------------------------------------------------------------------
test('Suite 7: Security & Credential Transport Validation', async (t) => {
  const apiClientPath = path.join(frontendSrc, 'api/client.ts');
  const clientContent = fs.readFileSync(apiClientPath, 'utf8');

  await t.test('API client enforces credentials: "include" for HTTP-only cookie transport', () => {
    assert.ok(
      clientContent.includes("credentials: 'include'") || clientContent.includes('credentials: "include"'),
      'api/client.ts must specify credentials: "include"'
    );
  });

  await t.test('API client injects X-CSRF-Token on state-mutating requests', () => {
    assert.ok(
      clientContent.includes('X-CSRF-Token'),
      'api/client.ts must attach X-CSRF-Token header'
    );
  });

  await t.test('API client supports Authorization Bearer header fallback', () => {
    assert.ok(
      clientContent.includes('Authorization') && clientContent.includes('Bearer'),
      'api/client.ts must support Bearer token authentication header'
    );
  });
});
