"""
Portfolio Metrics Extraction Tool

This module extracts financial and operating metrics from portfolio company 
PDF reports using Google Gemini AI for semantic understanding of varied document formats

The tool handles:
- Different report structures (tables, prose, mixed formats)
- Terminology variations ("Recognized Revenue" vs "Quarterly Revenue")
- Missing or non-applicable metrics (returns null)
- One-time items vs core metrics distinction

Aryan Verma, Janaury 2026 
"""

import os
import json
from google import genai
from pathlib import Path
import pandas as pd


def extract_text_from_pdf(pdf_path):
    """
    Extract all text content from a PDF file
    
    Uses pdfplumber to handle various PDF formats including those with tables
    and multi-column layouts

    Note:
    Does NOT handle scanned/image-based PDFs (would require OCR integration)
    
    Args:
        pdf_path (Path): Path to the PDF file to process
        
    Returns:
        str: Full text content from all pages, or None if extraction fails
        
    Note:
        Returns None rather than raising exceptions to allow graceful handling of problematic PDFs.
    """
    try:
        import pdfplumber
        
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            # Process each page sequentially to maintain document order
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    # Add newline between pages to preserve document structure
                    text += page_text + "\n"
        
        return text
    
    except ImportError:
        # Provide actionable error message for missing dependency
        print("ERROR: pdfplumber not installed. Install with: pip install pdfplumber")
        return None
    
    except Exception as e:
        # Catch any other error during PDF processing
        print(f"ERROR extracting text from {pdf_path}: {e}")
        return None


def extract_metrics_llm(company_name, pdf_text, client):
    """
    Extract structured financial metrics from PDF text using Google Gemini AI
    
    This function uses semantic understanding to handle:
    - Terminology variations (For example, "Revenue" vs "Recognized Revenue")
    - Format differences (tables vs prose)
    - Context awareness (distinguishing one-time items from core metrics)
    
    Args:
        company_name (str): Company identifier (used in error reporting)
        pdf_text (str): Full text content extracted from PDF
        client: Initialized Gemini client
        
    Returns:
        dict: Extracted metrics with keys:
            - company_name (str): Company identifier
            - recognized_revenue_m (float|None): Quarterly revenue in millions
            - arr_m (float|None): Annual recurring revenue in millions
            - gross_margin_pct (float|None): Gross margin percentage
            - total_headcount (int|None): Total employee count
            - logo_churn_pct (float|None): Customer churn percentage
            - cash_balance_m (float|None): Cash balance in millions
            - net_dollar_retention_pct (float|None): NDR percentage
            - error (str): Only present if extraction failed
            
    Note:
        Uses null for missing metrics to distinguish "not found" from "zero value"
    """
    
    # Construct detailed prompt with explicit formatting requirements
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
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        # Extract text from API response object
        response_text = response.text
        
        # Clean up response to handle Gemini's occasional markdown formatting
        # This is necessary because Gemini sometimes wraps JSON in code blocks even when explicitly instructed not to
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]  
        if response_text.startswith("```"):
            response_text = response_text[3:]   
        if response_text.endswith("```"):
            response_text = response_text[:-3]  
        response_text = response_text.strip()
        
        # Parse cleaned JSON string into Python dictionary
        metrics = json.loads(response_text)
        
        # Add company identifier to enable tracking in processing
        metrics['company_name'] = company_name
        
        return metrics
        
    except json.JSONDecodeError as e:
        # JSON parsing failed (Claude most likely returned malformed output)
        # Log the error with partial response for debugging
        print(f"  [WARNING] JSON parsing error for {company_name}: {e}")
        print(f"  Raw response: {response_text[:200]}...")
        return {
            'company_name': company_name,
            'error': 'JSON parsing failed'
        }
    
    except Exception as e:
        # Catch any other error
        print(f"  [WARNING] Error extracting metrics for {company_name}: {e}")
        return {
            'company_name': company_name,
            'error': str(e)
        }


def process_pdf_folder(folder_path, output_csv="extracted_metrics.csv"):
    """
    Process all PDF files in a folder and extract metrics to CSV
    
    This function does the following tasks:
    1. Validates API credentials and folder existence
    2. Discovers all PDF files in the target folder
    3. Extracts text and metrics from each PDF sequentially
    4. Aggregates results into a pandas DataFrame
    5. Exports to CSV for downstream analysis
    
    Args:
        folder_path (str): Path to folder containing PDF reports
        output_csv (str): Filename for output CSV (default: extracted_metrics.csv)
        
    Returns:
        pandas.DataFrame: Results with one row per company, or None if processing fails (For example, like missing an API key)
    """
    
    # Validate API key before attempting any processing
    # Fail fast rather than processing PDFs only to fail at API call
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("\n[ERROR] GOOGLE_API_KEY environment variable not set")
        print("Set it with: export GOOGLE_API_KEY='your-key-here'")
        print("Get a free API key at: https://aistudio.google.com/apikey\n")
        return None
    
    # Initialize Gemini client with validated key
    client = genai.Client(api_key=api_key)
    
    # Verify target folder exists before scanning for PDFs
    folder = Path(folder_path)
    if not folder.exists():
        print(f"\n[ERROR] Folder '{folder_path}' does not exist")
        print(f"Create it with: mkdir {folder_path}\n")
        return None
    
    # Discover all PDF files
    pdf_files = list(folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n[ERROR] No PDF files found in '{folder_path}'")
        print(f"Add your PDF reports to the '{folder_path}' folder and try again.\n")
        return None
    
    print(f"Found {len(pdf_files)} PDF file(s) to process\n")
    
    # Accumulator for results from all PDFs
    results = []
    
    # Process each PDF sequentially with progress indicator
    for i, pdf_file in enumerate(pdf_files, 1):
        # Use stem to get filename without .pdf extension (For example, "FleetLink" and not "FleetLink.pdf")
        company_name = pdf_file.stem
        print(f"[{i}/{len(pdf_files)}] Processing: {company_name}")
        
        # Step 1: Extract raw text from PDF
        pdf_text = extract_text_from_pdf(pdf_file)
        
        if pdf_text is None:
            # Extraction failed, skip this PDF and continue with others
            print(f"  [ERROR] Failed to extract text\n")
            continue
        
        # Sanity check: very short extractions usually indicate scanned PDFs
        if len(pdf_text) < 50:
            print(f"  [WARNING] Very little text extracted ({len(pdf_text)} chars)")
            print(f"  This might be a scanned PDF that needs OCR\n")
            continue
        
        print(f"  [OK] Extracted {len(pdf_text):,} characters of text")
        
        # Step 2: Use LLM to extract structured metrics from text
        metrics = extract_metrics_llm(company_name, pdf_text, client)
        
        # Confirm successful extraction (no error key in result)
        if 'error' not in metrics:
            print(f"  [OK] Extracted metrics successfully")
        
        # Append result even if extraction had errors (preserves company in output)
        results.append(metrics)
        print()
    
    # Check if any PDFs were successfully processed
    if not results:
        print("\n[ERROR] No results to save\n")
        return None
    
    # Convert list of dictionaries to pandas DataFrame for easier manipulation
    df = pd.DataFrame(results)
    
    # Reorder columns to put company_name first for readability
    # This makes the CSV easier to review in Excel/spreadsheet tools
    cols = ['company_name'] + [col for col in df.columns if col != 'company_name']
    df = df[cols]
    
    # Export to CSV without row indices 
    df.to_csv(output_csv, index=False)
    
    # Print results summary for immediate review
    print("=" * 70)
    print(f"SUCCESS: Results saved to {output_csv}")
    print("=" * 70)
    print("\nExtracted Metrics Summary:\n")
    print(df.to_string(index=False))
    
    # Print data completeness statistics
    # Helps identify which metrics are commonly missing across portfolio
    print("\n" + "=" * 70)
    print("Summary Statistics:")
    print("=" * 70)
    
    # Get all metric columns
    metric_columns = [col for col in df.columns if col not in ['company_name', 'error']]
    
    # Count non-null values for each metric across all companies
    for col in metric_columns:
        count = df[col].notna().sum()
        print(f"  {col}: {count}/{len(df)} companies")
    
    # Warn about any failed extractions
    if 'error' in df.columns:
        error_count = df['error'].notna().sum()
        if error_count > 0:
            print(f"\n  [WARNING] {error_count} extraction(s) had errors")
    
    print()
    
    return df


def main():
    """
    Main entry point for the portfolio metrics extraction tool
    
    The main method orchestrates:
    1. Display welcome banner
    2. Configure paths for input PDFs and output CSV
    3. Process all PDFs in the target folder
    4. Display next steps for user
    
    The function provides a user-friendly CLI experience with clear status messages and actionable next steps
    
    Returns:
        None: Results are written to CSV file specified in configuration
    """
    # Display banner for CLI user experience
    print("=" * 70)
    print(" " * 15 + "Portfolio Metrics Extraction Tool")
    print("=" * 70)
    print("\nExtracts financial and operating metrics from PDF reports using AI\n")
    
    pdf_folder = "sample_pdfs"
    output_file = "extracted_metrics.csv"
    
    # Execute main processing workflow
    df = process_pdf_folder(pdf_folder, output_file)
    
    # Display success message and guidance only if processing completed
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
