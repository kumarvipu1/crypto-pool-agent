"""GraphQL Subgraph Query Tool."""

from portia.tool import Tool, ToolRunContext
from portia.errors import ToolHardError
from pydantic import BaseModel, Field
import os
import pandas as pd
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from typing import Dict, Any, List, Optional
import json

class SubgraphQueryInput(BaseModel):
    """Input schema for the subgraph query tool."""
    query: str = Field(..., description="The GraphQL query to execute")
    output_file: str = Field(default="query_results.csv", description="Path to save the CSV file")
    flatten_nested: bool = Field(default=True, description="Whether to flatten nested data structures")

class SubgraphQueryOutput(BaseModel):
    """Output schema for the subgraph query tool."""
    file_path: str = Field(..., description="Path to the saved CSV file")
    row_count: int = Field(..., description="Number of rows in the dataset")
    columns: List[str] = Field(..., description="List of columns in the dataset")
    summary: Dict[str, Any] = Field(..., description="Statistical summary of the dataset")

class SubgraphQueryTool(Tool[SubgraphQueryOutput]):
    """Tool for querying subgraph data and saving to CSV.
    
    This tool executes GraphQL queries against a subgraph endpoint and saves the results
    to a CSV file. It can optionally flatten nested data structures and provides
    statistical summaries of the data.
    """
    
    id: str = "subgraph_query_tool"
    name: str = "Subgraph Query Tool"
    description: str = "Executes GraphQL queries against a subgraph and saves results to CSV"
    args_schema: type[BaseModel] = SubgraphQueryInput
    output_schema: tuple[str, str] = ("SubgraphQueryOutput", "Output containing file path and dataset summary")
    should_summarize: bool = False
    
    # Schema information
    schema_info: Dict[str, Any] = {}
    
    def __init__(self):
        super().__init__()
        transport = RequestsHTTPTransport(
            url=os.getenv("GRAPHQL_ENDPOINT"),
            verify=True,
            retries=3
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Load the local schema file
        self._load_schema()
    
    def _load_schema(self):
        """Load the schema from the local schema.graphql file."""
        try:
            schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schema.graphql")
            if os.path.exists(schema_path):
                with open(schema_path, "r") as f:
                    schema_content = f.read()
                
                # Extract entity information from the schema
                self.schema_info = self._parse_schema(schema_content)
                print(f"Loaded schema with {len(self.schema_info)} entities")
            else:
                print(f"Schema file not found at {schema_path}")
        except Exception as e:
            print(f"Error loading schema: {str(e)}")
    
    def _parse_schema(self, schema_content: str) -> Dict[str, Any]:
        """Parse the schema content to extract entity information."""
        entities = {}
        
        # Simple parsing to extract entity definitions
        lines = schema_content.split("\n")
        current_entity = None
        current_fields = []
        
        for line in lines:
            line = line.strip()
            
            # Check for entity definition
            if line.startswith("type ") and " @entity" in line:
                if current_entity:
                    entities[current_entity] = current_fields
                
                current_entity = line.split("type ")[1].split(" @entity")[0]
                current_fields = []
            
            # Check for field definition
            elif line and not line.startswith("#") and ":" in line and current_entity:
                field_name = line.split(":")[0].strip()
                field_type = line.split(":")[1].strip().split("!")[0].strip()
                current_fields.append({"name": field_name, "type": field_type})
        
        # Add the last entity
        if current_entity:
            entities[current_entity] = current_fields
        
        return entities
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the schema."""
        return self.schema_info
    
    def run(self, ctx: ToolRunContext, query: str, output_file: str = "query_results.csv", flatten_nested: bool = True) -> SubgraphQueryOutput:
        """
        Execute a GraphQL query and save results to CSV.
        
        Args:
            ctx: The tool run context containing the input parameters
            query: The GraphQL query to execute
            output_file: Path to save the CSV file
            flatten_nested: Whether to flatten nested data structures
            
        Returns:
            SubgraphQueryOutput: The output containing file path and dataset summary
            
        Raises:
            ToolHardError: If the query execution fails
        """
        try:
            # Execute the query
            response = self.client.execute(gql(query))

            # Flatten the top-level field dynamically
            top_level_key = list(response.keys())[0]
            data = response[top_level_key]

            # Flatten nested data structures if requested
            flat_data = []
            if len(data) > 0:
                for item in data:
                    flat_item = item.copy()
                    if flatten_nested:
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
                
                # Create output
                return SubgraphQueryOutput(
                    file_path=output_file,
                    row_count=len(df),
                    columns=df.columns.tolist(),
                    summary=df.describe().to_dict()
                )
            else:
                raise ToolHardError("Query returned no data")

        except Exception as e:
            raise ToolHardError(f"GraphQL query failed: {str(e)}") from e 