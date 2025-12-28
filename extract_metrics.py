import os
import json
import anthropic
from pathlib import Path
import pandas as pd


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
        metrics = extract_metrics_with_llm(company_name, pdf_text, client)
        
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