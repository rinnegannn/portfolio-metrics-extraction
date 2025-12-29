# Portfolio Metrics Extraction

Automated extraction of financial and operating metrics from portfolio company PDF reports using Claude AI.

---

## Approach & Decision-Making

### How I Approached the Problem

I broke the challenge into three questions:
1. How do I handle varied PDF formats and inconsistent terminology?
2. Which metrics matter most across different business models?
3. How do I deliver results quickly in a reviewable format?

**Key insight**: The core problem is **format variability**, not just data extraction. Traditional regex breaks when reports change structure. An LLM approach handles variations through semantic understanding.

### What I Chose to Implement and Why

**Architecture Decision: LLM-Powered Extraction**

I evaluated three approaches:

1. Regex (breaks with new formats)
2. NLP (needs pattern updates)
3. LLM (needs prompt updates)

**Decision**: LLM approach because it:
- Handles terminology variations automatically ("Revenue" = "Recognized Revenue")
- Understands context 
- Requires minimal code
- Scales easily (adding metrics = updating prompt, not rewriting code)

**Components Selected**:
- **pdfplumber** for text extraction (handles tables reliably)
- **Claude Sonnet 4** for semantic extraction 
- **pandas + CSV** for output 

**7 Metrics Chosen**:
- **Universal**: Revenue, Gross Margin, Headcount (all companies report these)
- **SaaS-specific**: ARR, Logo Churn, NDR (critical for subscription businesses)
- **Financial health**: Cash Balance (runway indicator)

These cover the metrics investors review in quarterly board meetings and allow comparison across portfolio companies despite different business models.

### Key Assumptions

1. **PDFs are text-based, not scanned images**
   - All sample PDFs are digitally generated with extractable text
   - *If wrong*: Would need OCR integration (adds ~30 min development)

2. **Revenue means recognized/quarterly revenue**
   - Not deferred revenue, bookings, or backlog
   - Most recent quarter if multiple periods shown

3. **Monetary values are in millions**
   - Standardized output for cross-company comparison
   - Currency differences noted but not converted

4. **Missing metrics return `null`, not zero**
   - Preserves data integrity (distinguishes "not found" from "zero value")
   - Non-SaaS companies won't have ARR - that's expected, not an error

5. **Out of scope for 1-2 hour POC**:
   - OCR for scanned PDFs
   - Quarter/year extraction (assumes filename convention)
   - Historical trend analysis
   - Currency conversion
   - Production infrastructure (logging, monitoring, retry logic)

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

**Requirements**: Python 3.8+, anthropic, pdfplumber, pandas

### 2. Set API Key
```bash
# Get free key at: https://console.anthropic.com
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# Windows PowerShell:
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

### 3. Add PDFs and Run
```bash
mkdir pdfs
# Copy PDF reports to pdfs/ folder
python extract_metrics.py
```

### 4. View Results
Open `extracted_metrics.csv` in Excel or Google Sheets.

---

## What Gets Extracted

| Metric | Description | Applicability |
|--------|-------------|---------------|
| **Revenue** | Recognized/Quarterly Revenue (millions) | All companies |
| **ARR** | Annual Recurring Revenue (millions) | SaaS only |
| **Gross Margin** | Gross profit percentage | All companies |
| **Headcount** | Total employees | All companies |
| **Logo Churn** | Customer churn rate (%) | SaaS only |
| **Cash Balance** | Cash on hand (millions) | Growth companies |
| **Net Dollar Retention** | Revenue retention + expansion (%) | SaaS only |

**Output Format**:
```csv
company_name,recognized_revenue_m,arr_m,gross_margin_pct,total_headcount,logo_churn_pct,cash_balance_m,net_dollar_retention_pct
FleetLink,9.3,,54,204,,,
NovaCloud,8.4,34.2,78,142,5.8,19.6,123
PeopleFlow,5.1,21.4,73,96,4.2,,118
```

---

## How It Works
```
PDF → Extract Text (pdfplumber) → Semantic Extraction (Claude AI) → Parse JSON → CSV Output
```

1. **Text Extraction**: pdfplumber extracts all text, preserving tables and layout
2. **LLM Processing**: Claude receives text with structured prompt specifying:
   - Exact metrics to extract
   - Output format (JSON with specific keys)
   - Instructions to ignore one-time items
   - Null handling for missing data
3. **Output Organization**: JSON parsed into pandas DataFrame, exported to CSV

**Why This Works Better Than Regex**:
- Handles "Revenue: $9.3M" and "recognized revenue totalled 6.8M" identically
- Distinguishes "$9.3M revenue" from "$0.6M warehouse exit cost"
- Adapts to new report formats automatically

---

## Limitations & Next Steps

### Current Limitations
- No OCR (scanned PDFs won't work)
- No quarter/year extraction (assumes filename has this)
- No currency conversion (values extracted as-is)
- Sequential processing (fine for <50 PDFs, would parallelize for scale)

### Production Evolution
**Phase 1** (1-2 weeks): Add quarter/year extraction, confidence scores, validation rules

**Phase 2** (1-2 months): OCR integration, parallel processing, QoQ comparison, dashboard integration

**At Scale**: Current manual process costs ~$33k/year for 500 companies. This approach: ~$3.4k/year (87% savings).

---

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
```bash
export ANTHROPIC_API_KEY='sk-ant-...'  # or $env: on Windows
```

**"No PDF files found"**
```bash
mkdir pdfs
# Add PDF files to pdfs/ folder
```

**"Very little text extracted"**
- PDF is likely scanned/image-based (needs OCR, not in scope for POC)

---

## Author

Built for Sagard's Technical Challenge

**Aryan Verma** | verma63@mcmaster.ca