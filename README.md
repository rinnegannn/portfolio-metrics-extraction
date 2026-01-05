# Portfolio Metrics Extraction

Automated extraction of financial and operating metrics from portfolio company PDF reports using Gemini AI.

## Table of Contents
- [Demo Video](#demo-video)
- [Approach & Decision-Making](#approach--decision-making)
  - [The Problem](#the-problem)
  - [Solution Strategy](#solution-strategy)
  - [Approaches Considered](#approaches-considered)
  - [Metric Selection Strategy](#metric-selection-strategy)
  - [Key Assumptions](#key-assumptions)
  - [Limitations & Next Steps](#limitations--next-steps)
- [Quick Start](#quick-start)
- [What Gets Extracted](#what-gets-extracted)
- [How It Works](#how-it-works-system-pipeline)
- [Troubleshooting](#troubleshooting)
- [Author](#author)


## Demo Video

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

I broke the challenge into four key questions:
1. How do I handle varied PDF structures and complex layouts?
2. Which metrics matter most across different business models?
3. How do I extract data accurately despite inconsistent terminology?
4. How do I deliver results quickly in a reviewable format?

### Solution Strategy
To address these questions, I broke the technical implementation into three logical phases:

1. **PDF to Raw Text**: 
   PDFs are designed for people, however are not easily interpreted by machines. Converting them to text removes formatting like layouts and fonts, creating a clean input that allows the rest of the pipeline to focus on the actual content.

2. **Raw Text to Structured JSON**: 
   Rather than writing 100+ rules for every phrasing variation (eliminating the need for fragile regex or custom NLP models), I leverage an LLM which replaces hard-coded rules with semantic understanding. It can distinguish between *Quarterly Revenue* and *Interest Expense* by context, just like a human analyst would, and formatted as machine-readable JSON.

3. **Structured JSON to CSV**: 
   JSON is ideal for machine processing but impractical for direct human analysis. This final step converts the structured data into a CSV format, enabling Sagard’s team to immediately compare performance across the portfolio in Excel or integrate the data into BI platforms like Tableau and PowerBI.

### Approaches Considered

I evaluated three main technologies for the extraction process, prioritizing accuracy and scalability:

| Approach | Pros | Cons |
| :--- | :--- | :--- |
| **Regex & Rule-Based** | Deterministic, no API costs, transparent logic | **Fragile to layout variations**, high maintenance, no semantic awareness |
| **NLP** | More flexible than regex, better context awareness (can identify entities)| **Heavy pattern engineering**, high maintenance, limited reasoning for complex tables |
| **LLMs (Selected)** | **Handles messy data**, true semantic understanding, highly extensible | API cost, external dependency, potential for "hallucinations" |

**Decision**: **LLM-Powered Extraction** because it handles terminology variations automatically ("Revenue" = "Recognized Revenue") and scales easily (adding metrics only requires a prompt update).

### Implementation Details
- **pdfplumber**: Handles page-by-page text extraction while preserving layout structure (crucial for multi-column reports).
- **Gemini 2.0 Flash**: Transforms unstructured text into schema-validated JSON using reasoning.
- **pandas + CSV**: Cleans and organizes the data into a portable, spreadsheet-ready format for immediate analysis.

### Why JSON?
While the final output is a CSV, JSON is used as the intermediate format between the AI and the spreadsheet to ensure data integrity:
- **Schema Enforcement**: Guarantees that the AI returns exact keys (e.g., `arr_m`) every time, preventing broken columns in the final report.
- **Type Safety**: Ensures that numeric values stay as numbers and missing data is explicitly marked as `null` rather than empty strings.
- **Validation**: Allows the system to "fail fast" if the AI returns a malformed response, the script can catch the error before it corrupts the final dataset.

### Why CSV?
CSV was selected as the output format to prioritize **portability** and **ease of use** for the end user:
- **Finance-Friendly**: Allows immediate review and manipulation in Excel or Google Sheets, the primary tools for investment analysts.
- **Aggregatable**: Enables easy comparison across multiple portfolio companies in a single view.
- **Universally Compatible**: Can be directly imported into CRM systems (Salesforce), databases, or BI tools like Tableau and PowerBI without any extra processing.

### Metric Selection Strategy

I chose these 7 core metrics to provide a clear picture of both general business performance and SaaS-specific growth:

| Category | Metrics | Strategic Value |
| :--- | :--- | :--- |
| **Universal** | Revenue, Gross Margin, Headcount | Key indicators of scale and operational efficiency. |
| **SaaS-Specific** | ARR, Logo Churn, NDR | Critical for tracking subscription growth and customer retention. |
| **Financials** | Cash Balance | Used to track available cash and funding needs. |

These metrics were chosen based on:
- **Universal Relevance**: Metrics that matter across almost any business model.
- **SaaS Specifics**: Key indicators specifically for subscription-based companies.
- **Usefulness**: Data points that are the most helpful for a quick performance review.

### Key Assumptions

* **English Language**: The reports are written in English.
* **Text-based PDFs**: The reports are digitally generated with extractable text, not scanned images.
* **Extraction vs. Computation**: The goal is to extract metrics as reported, not to compute or derive new ones.
* **Data Integrity**: Missing or non-applicable metrics return `null` rather than a guessed value or zero.

### Limitations & Next Steps

While this POC proves the core concept, I would prioritize the following for a production-ready version:

- **OCR Integration**: Add support for scanned or image-based PDFs.
- **Parallel Processing**: Move from sequential to concurrent processing to handle large portfolios.
- **Automated Verification**: Implement confidence scores, range checks, and anomaly detection to flag outlier results for human review.
- **User Interface**: Build a web-based dashboard to make the tool more accessible for non-technical analysts.
- **Persistence & Trend Analysis**: Move from CSV to a cloud database to enable historical tracking and cross-portfolio comparisons.

All of these were intentionally deferred to focus the immediate effort on perfecting the **semantic extraction** logic.

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
