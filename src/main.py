import argparse
from agent import run_agent
from markdown_pdf import MarkdownPdf, Section
import os
from datetime import datetime

def run_pipeline(user_query: str):
    """
    Run the liquidity analysis pipeline.
    
    Args:
        user_query (str): The user's query about liquidity analysis
        
    Returns:
        dict: A dictionary containing the results of the analysis
    """
    # Create output directory if it doesn't exist
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Run the agent
    result = run_agent(user_query)
    
    # Generate PDF report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(output_dir, f"liquidity_analysis_{timestamp}.pdf")
    
    pdf = MarkdownPdf()
    pdf.add_section(Section(result.markdown_report))
    pdf.save(pdf_path)
    
    # Return results
    return {
        "pdf_path": pdf_path,
        "html_paths": result.html_path,
        "png_paths": result.png_path,
        "csv_path": result.csv_path,
        "metrics": result.metrics_dict
    }

def main():
    parser = argparse.ArgumentParser(description="Run liquidity analysis pipeline")
    parser.add_argument("query", help="The user query for liquidity analysis")
    args = parser.parse_args()
    
    results = run_pipeline(args.query)
    
    print("\nAnalysis Results:")
    print(f"PDF Report: {results['pdf_path']}")
    print("\nHTML Charts:")
    for path in results['html_paths']:
        print(f"- {path}")
    print("\nPNG Charts:")
    for path in results['png_paths']:
        print(f"- {path}")
    print(f"\nCSV Data: {results['csv_path']}")
    print("\nMetrics:")
    print(results['metrics'])

if __name__ == "__main__":
    main() 