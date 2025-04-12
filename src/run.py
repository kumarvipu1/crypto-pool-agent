import os
import sys
import argparse
from dotenv import load_dotenv
from main import run_pipeline

# Load environment variables
load_dotenv()

def main():
    """Run the liquidity analysis pipeline"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze liquidity data from subgraphs')
    parser.add_argument('query', help='The query to analyze')
    parser.add_argument('--schema', help='Path to the GraphQL schema file', default='schema.graphql')
    args = parser.parse_args()
    
    # Load schema from file
    with open(args.schema, "r") as f:
        schema = f.read()
    
    # Run pipeline
    results = run_pipeline(args.query, schema)
    
    # Print results
    print(f"Analysis complete. Report saved to {results['pdf_path']}")
    print(f"HTML charts: {', '.join(results['html_path'])}")
    print(f"PNG charts: {', '.join(results['png_path'])}")

if __name__ == "__main__":
    main() 