import os
import json
import anthropic
from pathlib import Path
import pandas as pd

def extract_text_from_pdf(pdf_path):
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return text
    
    except ImportError:
        print("ERROR: pdfplumber not installed. Install with: pip install pdfplumber")
        return None
    
    except Exception as e:
        print(f"ERROR extracting text from {pdf_path}: {e}")
        return None
    

def extract_metrics_llm(company_name, pdf_text, client):
    
    prompt = f"""You are analyzing a portfolio company quarterly report. Extract the following key metrics from the text below.

IMPORTANT INSTRUCTIONS:
1. Extract ONLY the core operating metrics, NOT one-time items or non-core financial details
2. For revenue and cash, extract the numeric value in millions (For example, if you see "$9.3M" or "9.3M", return 9.3)
3. For percentages, return just the number (For example, if you see "54%", return 54)
4. For headcount, return the integer number
5. If a metric is not found or not applicable for this company, return null
6. Be precise, make sure you're extracting the right metric (For example, do not confuse one-time costs with revenue)

METRICS TO EXTRACT:
- recognized_revenue_m: Recognized Revenue, Quarterly Revenue, or similar (in millions, numeric only)
- arr_m: Annual Recurring Revenue or ARR (in millions, numeric only)
- gross_margin_pct: Gross Margin as a percentage (numeric only, without % sign)
- total_headcount: Total number of employees (integer)
- logo_churn_pct: Customer churn rate, logo churn (as percentage, numeric only)
- cash_balance_m: Cash balance or cash on hand (in millions, numeric only)
- net_dollar_retention_pct: Net Dollar Retention or NDR (as percentage, numeric only)

Return your response as a valid JSON object with these exact keys. Use null for any metric not found.

COMPANY REPORT TEXT:
{pdf_text}

Return ONLY the JSON object, no other text."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the text response
        response_text = message.content[0].text
        
        # Clean up response (remove markdown code blocks if present)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        metrics = json.loads(response_text)
        
        # Add company name to results
        metrics['company_name'] = company_name
        
        return metrics
        
    except json.JSONDecodeError as e:
        print(f"  [WARNING] JSON parsing error for {company_name}: {e}")
        print(f"  Raw response: {response_text[:200]}...")
        return {
            'company_name': company_name,
            'error': 'JSON parsing failed'
        }
    
    except Exception as e:
        print(f"  [WARNING] Error extracting metrics for {company_name}: {e}")
        return {
            'company_name': company_name,
            'error': str(e)
        }


def process_pdf_folder(folder_path, output_csv="extracted_metrics.csv"):
    
    # Initialize Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n[ERROR] ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: $env:ANTHROPIC_API_KEY = 'your-key-here'")
        print("Get a free API key at: https://console.anthropic.com\n")
        return None
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Find all PDF files
    folder = Path(folder_path)
    if not folder.exists():
        print(f"\n[ERROR] Folder '{folder_path}' does not exist")
        print(f"Create it with: mkdir {folder_path}\n")
        return None
    
    pdf_files = list(folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n[ERROR] No PDF files found in '{folder_path}'")
        print(f"Add your PDF reports to the '{folder_path}' folder and try again.\n")
        return None
    
    print(f"Found {len(pdf_files)} PDF file(s) to process\n")
    
    results = []
    
    # Process each PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        # Filename without extension
        company_name = pdf_file.stem  
        print(f"[{i}/{len(pdf_files)}] Processing: {company_name}")
        
        # Step 1: Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_file)
        
        if pdf_text is None:
            print(f"  [ERROR] Failed to extract text\n")
            continue
        
        if len(pdf_text) < 50:
            print(f"  [WARNING] Very little text extracted ({len(pdf_text)} chars)")
            print(f"  This might be a scanned PDF that needs OCR\n")
            continue
        
        print(f"  [OK] Extracted {len(pdf_text):,} characters of text")
        
        # Step 2: Extract metrics using LLM
        metrics = extract_metrics_llm(company_name, pdf_text, client)
        
        if 'error' not in metrics:
            print(f"  [OK] Extracted metrics successfully")
        
        results.append(metrics)
        print()
    
    # Convert to DataFrame and save
    if not results:
        print("\n[ERROR] No results to save\n")
        return None
    
    df = pd.DataFrame(results)
    
    # Reorder columns to put company_name first
    cols = ['company_name'] + [col for col in df.columns if col != 'company_name']
    df = df[cols]
    
    # Save to CSV
    df.to_csv(output_csv, index=False)
    
    print("=" * 70)
    print(f"SUCCESS: Results saved to {output_csv}")
    print("=" * 70)
    print("\nExtracted Metrics Summary:\n")
    print(df.to_string(index=False))
    
    # Print summary statistics
    print("\n" + "=" * 70)
    print("Summary Statistics:")
    print("=" * 70)
    
    metric_columns = [col for col in df.columns if col not in ['company_name', 'error']]
    
    for col in metric_columns:
        count = df[col].notna().sum()
        print(f"  {col}: {count}/{len(df)} companies")
    
    if 'error' in df.columns:
        error_count = df['error'].notna().sum()
        if error_count > 0:
            print(f"\n  [WARNING] {error_count} extraction(s) had errors")
    
    print()
    
    return df
    

def main():
    """
    Main execution function.
    """
    print("=" * 70)
    print(" " * 15 + "Portfolio Metrics Extraction Tool")
    print("=" * 70)
    print("\nExtracts financial and operating metrics from PDF reports using AI\n")
    
    # Configuration
    pdf_folder = "pdfs"
    output_file = "extracted_metrics.csv"
    
    # Process PDFs
    df = process_pdf_folder(pdf_folder, output_file)
    
    if df is not None:
        print("=" * 70)
        print("SUCCESS: Extraction Complete!")
        print("=" * 70)
        print(f"\nNext steps:")
        print(f"  1. Open {output_file} in Excel or Google Sheets")
        print(f"  2. Review extracted metrics")
        print(f"  3. Add more PDFs to '{pdf_folder}' folder and run again")
        print()


if __name__ == "__main__":
    main()