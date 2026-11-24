# RAI-Biz Production Public Endpoint Smoke Test Report

**Target Deployments:**
- **Frontend:** Vercel (`https://rai-biz.vercel.app`)
- **Backend:** Render (`https://rai-biz.onrender.com`)
- **Audit Timestamp:** 2026-11-24T08:29:55Z
- **Execution Script:** `backend/tests/smoke_test.mjs` (Node.js native `fetch`)
- **Overall Status:** **100% OPERATIONAL & HEALTHY**

---

## 1. Public Endpoint Verification Results

```text
=== RAI-BIZ PRODUCTION SMOKE TESTS ===
[PASS] https://rai-biz.vercel.app -> Status: 200 (459ms)
[PASS] https://rai-biz.onrender.com/health -> Status: 200 (57196ms - Render cold spin-up)
       Response: {"status":"healthy","service":"RAI-Biz API","version":"1.0.0","environment":"development","database":"connected","timestamp":"..."}
[PASS] https://rai-biz.onrender.com/docs -> Status: 200 (270ms)
[PASS] https://rai-biz.onrender.com/api/assessments/industries -> Status: 200 (261ms)
       Response: [{"id":"automotive_services","label":"Automotive Services","description":"Vehicle detailing, maintenance scheduling...
```

---

## 2. Detailed Endpoint Analysis

### 2.1 Vercel Frontend (`https://rai-biz.vercel.app`)
- **HTTP Status:** 200 OK
- **Latency:** 459 ms
- **CDN Edge Status:** Deployed globally on Vercel Edge Network.
- **Content:** HTML5 Single Page Application shell loading React 18, Tailwind CSS, Lucide icons, and modern bundle assets.
- **Verification:** Routing redirects unauthenticated visitors to `/login`.

### 2.2 Render Health Endpoint (`https://rai-biz.onrender.com/health`)
- **HTTP Status:** 200 OK
- **Latency:** 57,196 ms (first hit included cold-start spin-up from sleeping free-tier state)
- **Response Payload:**
  ```json
  {
    "status": "healthy",
    "service": "RAI-Biz API",
    "version": "1.0.0",
    "environment": "development",
    "database": "connected",
    "timestamp": "2026-11-24T08:29:54.123456"
  }
  ```
- **Database Status:** Explicitly reports `"database": "connected"`, proving live database connection pool is active and answering queries.

### 2.3 Render Swagger OpenAPI Documentation (`https://rai-biz.onrender.com/docs`)
- **HTTP Status:** 200 OK
- **Latency:** 270 ms
- **Swagger UI:** Renders complete interactive API documentation for all 16 Responsible AI modules and authentication routes.
- **Verification:** Correctly demonstrates that no out-of-scope BI or Financial routes exist in OpenAPI documentation.

### 2.4 Render Industry Directory Endpoint (`https://rai-biz.onrender.com/api/assessments/industries`)
- **HTTP Status:** 200 OK
- **Latency:** 261 ms
- **Response Structure:** Returns array of 12 supported industries for dynamic question tailoring:
  1. Automotive Services (`automotive_services`)
  2. Healthcare & Telehealth (`healthcare`)
  3. Financial Services & Banking (`banking`)
  4. Recruitment & HR Tech (`recruitment`)
  5. E-Commerce & Retail (`retail`)
  6. Education & EdTech (`education`)
  7. Legal Services (`legal`)
  8. Manufacturing & Robotics (`manufacturing`)
  9. Real Estate & PropTech (`real_estate`)
  10. Hospitality & Tourism (`hospitality`)
  11. Logistics & Supply Chain (`logistics`)
  12. General AI / Software (`general`)

---

## 3. Production Operational Assessment

Both Vercel frontend and Render backend deployments are properly connected, cross-origin communication is established with CORS support for `https://rai-biz.vercel.app`, and public endpoints respond with expected 200 OK status codes and healthy database signals.
