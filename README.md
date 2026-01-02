# Portfolio Metrics Extraction

Automated extraction of financial and operating metrics from portfolio company PDF reports using Gemini AI.

## 📹 Demo Video

[![Watch the Demo](https://img.youtube.com/vi/ZEI-DJSw5DM/0.jpg)](https://youtu.be/ZEI-DJSw5DM)

*Click the image above to watch a walkthrough of the project*

---

## Approach & Decision-Making

### The Problem
Sagard receives quarterly PDF reports from portfolio companies that vary widely in **structure**, **terminology**, and **metric availability**. Manual extraction is time-consuming, error-prone, and not scalable.

### Goal (1-2 Hour POC)
1. Build a simple, end-to-end pipeline
2. Focus on accuracy over completeness
3. Handle messy, inconsistent PDFs
4. Produce structured output suitable for review

### How I Approached the Problem

I broke the challenge into three questions:
1. How do I handle varied PDF formats and inconsistent terminology?
2. Which metrics matter most across different business models?
3. How do I deliver results quickly in a reviewable format?

### Solution Strategy
To solve these, I broke the technical implementation into three logical phases:

1. **Bridge the Format Gap (PDF to Text)**: 
   PDFs are designed for humans, not machines. By first converting the PDF into a raw text stream, I strip away "noise" (layout, colors, fonts). This creates a clean input that lets the LLM focus purely on the meaning of the words.

2. **Semantic Interpretation (Text to JSON)**:
   Rather than writing 100+ rules for every phrasing variation, I leverage an LLM which replaces rigid, hard-coded rules with flexible semantic understanding. It can distinguish between *Quarterly Revenue* and *Interest Expense* by context, just like a human analyst would, and formatted as machine-readable JSON.

3. **User-Centric Delivery (JSON to CSV)**:
   JSON is great for systems, but it is not friendly for analysts. The final step converts the extracted data into a CSV, enabling Sagard’s team to immediately compare performance across the entire portfolio in Excel.

### Approaches Considered

I evaluated three technical paths, prioritizing accuracy and scalability:

| Approach | Pros | Cons |
| :--- | :--- | :--- |
| **Regex & Rule-Based** | Deterministic, no API costs, transparent logic | **Fragile to layout variations**, high maintenance, no semantic awareness |
| **NLP** | More flexible than regex, better context awareness | **Heavy pattern engineering**, limited reasoning for complex tables |
| **LLMs (Selected)** | **Handles messy data**, true semantic understanding, highly extensible | API cost, requires internet, potential for "hallucinations" |

**Decision**: **LLM-Powered Extraction** because it handles terminology variations automatically ("Revenue" = "Recognized Revenue") and scales easily (adding metrics only requires a prompt update).

### Implementation Details
- **pdfplumber**: Used because it can accurately read complex PDF layouts. This is important for financial reports where numbers and labels are spread across multiple columns, and keeping their positions aligned prevents incorrect data extraction.
- **Gemini 2.0 Flash**: Chosen for its fast performance and strong reasoning abilities. Its structured response feature allows the model to return clean, predictable JSON, making the extracted metrics more reliable without relying on fragile text-matching rules.
- **pandas + CSV**: Used to convert the structured output into a format analysts can easily work with. Pandas cleans and organizes the data, and exporting to CSV makes it ready for analysis, reporting, or financial modeling.

### Why JSON?
While the final output is a CSV, JSON is used as the intermediate format between the AI and the spreadsheet to ensure data integrity:
- **Schema Enforcement**: Guarantees that the AI returns exact keys (e.g., `arr_m`) every time, preventing broken columns in the final report.
- **Type Safety**: Ensures that numeric values stay as numbers and missing data is explicitly marked as `null` rather than empty strings.
- **Validation**: Allows the system to "fail fast" if the AI returns a malformed response, the script can catch the error before it corrupts the final dataset.

### Why CSV?
CSV was selected as the output format to prioritize **portability** and **ease of use** for the end user:
- **Finance-Friendly**: Allows immediate review and manipulation in Excel or Google Sheets, the primary tools for investment analysts.
- **Aggregatable**: Enables easy comparison across multiple portfolio companies in a single view.
- **System Agnostic**: Can be easily imported into downstream databases, CRMs (like Salesforce), or BI tools without complex parsing.

### Metric Selection Strategy

I selected 7 core metrics to balance broad financial visibility with deep-dive SaaS analytics:

| Category | Metrics | Strategic Value |
| :--- | :--- | :--- |
| **Universal** | Revenue, Gross Margin, Headcount | Baseline indicators of scale and operational efficiency. |
| **SaaS-Specific** | ARR, Logo Churn, NDR | Critical signals for subscription health and retention. |
| **Financial Health** | Cash Balance | Essential for monitoring runway and capital requirements. |

This selection enables standardized benchmarking across the portfolio, focusing on the data points most critical for quarterly board-level reviews.

### Key Assumptions

1. **PDFs are text-based, not scanned images**
   - All sample PDFs are digitally generated with extractable text
   - *If wrong*: Would need OCR integration

2. **Revenue means recognized/quarterly revenue**
   - Not deferred revenue, bookings, or backlog
   - Most recent quarter if multiple periods shown

3. **Monetary values are in millions**
   - Standardized output for cross-company comparison
   - Currency differences noted but not converted

4. **Missing metrics return `null` rather than zero**
   - Preserves data integrity by distinguishing between a reported zero and missing information
   - Accounts for business model variations (for example, non-SaaS companies will correctly show `null` for ARR rather than an incorrect zero)

5. **Out of scope**:
   - OCR for scanned images
   - Automated period/date detection
   - Currency conversion
   - Production-grade infrastructure (logging, monitoring, retries)

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

**Requirements**: Python 3.8+, `google-genai`, `pdfplumber`, `pandas`

### 2. Set API Key
```bash
# Get free key at: https://aistudio.google.com/app/apikey
export GOOGLE_API_KEY='your-api-key-here'

# Windows PowerShell:
$env:GOOGLE_API_KEY = "your-api-key-here"
```

### 3. Add PDFs and Run
```bash
mkdir sample_pdfs
# Copy PDF reports to sample_pdfs/ folder
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

## How It Works (System Pipeline)
```
PDF → Extract Text (pdfplumber) → Semantic Extraction (Gemini AI) → Parse JSON → CSV Output
```

1. **Text Extraction**: pdfplumber extracts all text, preserving tables and layout
2. **LLM Processing**: Gemini receives text with structured prompt specifying:
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

**"GOOGLE_API_KEY not set"**
```bash
export GOOGLE_API_KEY='your-api-key-here' 
```

**"No PDF files found"**
```bash
mkdir sample_pdfs
```

**"Very little text extracted"**
- PDF is likely scanned/image-based (needs OCR, not in scope for POC)

---

## Author

Built for Sagard's Technical Challenge

**Aryan Verma** | verma63@mcmaster.ca
```
