import requests
from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext
import os
import json
import pandas as pd
from typing import Dict, Any
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

class SubgraphQuerySchema(BaseModel):
    gql_query: str = Field(..., description="The GraphQL query to run")
    output_file: str = Field(..., description="The name of the CSV file to save the results")

class SubgraphQueryTool(Tool):
    """Tool for querying subgraph data and saving to CSV"""
    
    def __init__(self):
        super().__init__(
            name="subgraph_query_tool",
            description="Runs a GraphQL query on the subgraph and saves results to CSV"
        )
    
    def execute(self, query: str, output_file: str = "query_results.csv") -> str:
        """
        Execute a GraphQL query and save results to CSV.
        
        Args:
            query: The GraphQL query to execute
            output_file: Path to save the CSV file
            
        Returns:
            str: Status message with dataset summary
        """
        # Set up transport and client
        transport = RequestsHTTPTransport(url=os.getenv("GRAPHQL_ENDPOINT"), verify=True, retries=3)
        client = Client(transport=transport, fetch_schema_from_transport=True)

        try:
            # Execute the query
            response = client.execute(gql(query))

            # Flatten the top-level field dynamically
            top_level_key = list(response.keys())[0]
            data = response[top_level_key]

            # Flatten nested data structures
            flat_data = []
            if len(data) > 0:
                for item in data:
                    flat_item = item.copy()
                    # Handle nested token data
                    if "token0" in item and isinstance(item["token0"], dict):
                        flat_item.update({
                            "token0_id": item["token0"].get("id"),
                            "token0_symbol": item["token0"].get("symbol"),
                            "token0_name": item["token0"].get("name"),
                        })
                        del flat_item["token0"]
                    if "token1" in item and isinstance(item["token1"], dict):
                        flat_item.update({
                            "token1_id": item["token1"].get("id"),
                            "token1_symbol": item["token1"].get("symbol"),
                            "token1_name": item["token1"].get("name"),
                        })
                        del flat_item["token1"]
                    flat_data.append(flat_item)

                # Convert to DataFrame and save
                df = pd.DataFrame(flat_data)
                df.to_csv(output_file, index=False)
                return f"Saved query results to {output_file}\nDataset summary:\n{df.describe()}"

        except Exception as e:
            return f"GraphQL query failed: {str(e)}" 