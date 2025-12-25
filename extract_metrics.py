import os
import json
import anthropic
from pathlib import Path
import pandas as pd


def process_pdf_folder(folder_path, output_csv):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nANTHROPIC_API_KEY environment variable not set.")
        return None
    client = anthropic.Anthropic(api_key=api_key)

    # Find all PDF files
    folder = Path(folder_path)
    if not folder.exists():
        print(f"\nError: Folder '{folder_path}' does not exist")
        return None

    pdf_files = list(folder.rglob("*.pdf"))
    if not pdf_files:
        print(f"\nNo PDF files found in folder '{folder_path}'")
        return None
    
    



def main():
    print("=" * 70)
    print(" " * 15 + "Portfolio Metrics Extraction Tool")
    print("=" * 70)
    print("\nExtracts financial and operating metrics from PDF reports using AI\n")

if __name__ == "__main__":
    main()