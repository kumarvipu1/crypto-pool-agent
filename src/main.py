"""Main entry point for the crypto pool analysis agent."""

import asyncio
import argparse
from src.agent import run_agent

async def main():
    """Run the crypto pool analysis agent."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Crypto Pool Analysis Agent")
    parser.add_argument("query", help="The query about liquidity analysis")
    parser.add_argument("--pool", help="Pool address to analyze")
    parser.add_argument("--start-time", type=int, help="Start time for analysis")
    parser.add_argument("--end-time", type=int, help="End time for analysis")
    args = parser.parse_args()

    # Run the agent
    response = await run_agent(
        user_prompt=args.query,
        pool_address=args.pool,
        start_time=args.start_time,
        end_time=args.end_time
    )

    # Print the markdown report
    print("\nAnalysis Report:")
    print("=" * 80)
    print(response.markdown_report)
    print("=" * 80)

    # Print file paths
    print("\nGenerated Files:")
    print(f"CSV Data: {response.csv_path}")
    print(f"PDF Report: {response.pdf_path}")
    print("\nHTML Charts:")
    for path in response.html_paths:
        print(f"  - {path}")
    print("\nPNG Charts:")
    for path in response.png_paths:
        print(f"  - {path}")

if __name__ == "__main__":
    asyncio.run(main()) 