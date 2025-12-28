import os
import json
import anthropic
from pathlib import Path
import pandas as pd


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
        print(f"JSON parsing error for {company_name}: {e}")
        print(f"Raw response: {response_text[:200]}...")
        return {
            'company_name': company_name,
            'error': 'JSON parsing failed'
        }
    
    except Exception as e:
        print(f"Error extracting metrics for {company_name}: {e}")
        return {
            'company_name': company_name,
            'error': str(e)
        }


def process_pdf_folder(folder_path, output_csv="extracted_metrics.csv"):
    
    # Initialize Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nError: ANTHROPIC_API_KEY environment variable not set")
        return None
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Find all PDF files
    folder = Path(folder_path)
    if not folder.exists():
        print(f"\nError: Folder '{folder_path}' does not exist")
        return None
    
    pdf_files = list(folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\nNo PDF files found in '{folder_path}'")
        print(f"Add your PDF reports to the '{folder_path}' folder and try again.\n")
        return None
    
    print(f"Found {len(pdf_files)} PDF file(s) to process\n")
    
    results = []
    
    # Process each PDF
    for pdf_file in pdf_files:
        # Filename without extension
        company_name = pdf_file.stem  
        print(f"Processing: {company_name}")
        
        # Firstly, extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_file)
        
        if pdf_text is None:
            print(f"Failed to extract text\n")
            continue
        
        if len(pdf_text) < 50:
            print(f"Warning: Very little text extracted ({len(pdf_text)} chars)")
            print(f"This might be a scanned PDF that needs OCR\n")
            continue
        
        print(f"Extracted {len(pdf_text):,} characters of text")
        
        # Step 2: Extract metrics using LLM
        metrics = extract_metrics_llm(company_name, pdf_text, client)
        
        if 'error' not in metrics:
            print(f"Extracted metrics successfully")
        
        results.append(metrics)
        print()
    
    # Convert to DataFrame and save
    if not results:
        print("\nNo results to save\n")
        return None
    
    df = pd.DataFrame(results)
    
    # Reorder columns to put company_name first
    cols = ['company_name'] + [col for col in df.columns if col != 'company_name']
    df = df[cols]
    
    # Save to CSV
    df.to_csv(output_csv, index=False)
    
    print("=" * 70)
    print(f"Results saved to: {output_csv}")
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
            print(f"\n{error_count} extraction(s) had errors")
    
    print()
    
    return df
    

def main():
    print("=" * 70)
    print(" " * 15 + "Portfolio Metrics Extraction Tool")
    print("=" * 70)
    print("\nExtracts financial and operating metrics from PDF reports using AI\n")

if __name__ == "__main__":
    main()