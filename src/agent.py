from portia import Agent, RunContext, ModelRetry
from portia.models import openai
from portia.tool import Tool
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import json
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from io import StringIO
from contextlib import redirect_stdout
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import numpy as np

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAIModel('gpt-4', api_key=os.getenv('OPENAI_API_KEY'))

@dataclass
class AgentState:
    user_query: str

class AgentResponse:
    def __init__(self, markdown_report: str, csv_path: str, metrics_dict: str, 
                 html_path: List[str], png_path: List[str], pdf_path: str):
        self.markdown_report = markdown_report
        self.csv_path = csv_path
        self.metrics_dict = metrics_dict
        self.html_path = html_path
        self.png_path = png_path
        self.pdf_path = pdf_path

# Create Portia agent
agent = Agent(model=client, deps_type=AgentState, result_type=AgentResponse)

# Get current date
current_date = datetime.now().strftime("%Y-%m-%d")

@agent.system_prompt
def get_agent_system_prompt(ctx: RunContext[AgentState]):
    prompt = f"""
    You are an analyst for a crypto trading company. Your goal is to analyze liquidity of a crypto token and provide users important information relevant to the user query with a detailed report.
    The user will provide you a query and schema of the liquidity information of the crypto token. You will access the relevant tools to help you retrieve the liquidity information of the crypto token.
    The user query is:\n {ctx.deps.user_query} and the current date is {current_date}\n
    
    You have access to the following tools to perform analysis:
    - query_liquidity_data : to retrieve the liquidity information of the crypto token
    - metric_calculator : to run the python code to calculate the metrics
    - get_column_list : to retrieve the column list from the json file
    - graph_generator : to generate the graph
    
    Follow the following steps:
    1. Understand the user query and identify what liquidity information the user is looking for
    2. Based on the schema, frame a graphql query to retrieve the liquidity information of the crypto token
    3. Use the query_liquidity_data tool to access the relevant liquidity information of the crypto token
    4. Use the get_column_list tool to retrieve the column list from the csv file, use these columns for metric calculation and visualization
    5. List out the metrics that you can calculate from the liquidity information and data summary
    6. Use the metric_calculator tool to run the python code using the tabulate library to calculate the metrics, use print statement to read the calculated metrics in tabular format
    7. Plot charts for the metrics calculated in step 6 using plotly express library and save them in html and png format. Use the graph_generator tool to execute the code and save the output in html and png format
    8. Analyze the liquidity information thoroughly, focusing the information asked by the user in the query
    9. Create a comprehensive markdown report, use your best judgement to structure the report. Bold the key information asked by the user in the report.
    
        [Title of the report]
        [Date of the report]
        [Structured content as per the user query]
    10. Generate a hypothetical pdf file name as <suitable_name>_<date>.pdf of the report, just name.
    11. IMPORTANT: If the information is inferred and not directly present in the document, give a disclaimer that the information is inferred and not directly present in the document.
    12. Stop the execution after the report is generated.
    """
    return prompt

@agent.tool
async def get_column_list(
    ctx: RunContext[None],
    file_name: str
):
    """
    Use this tool to get the column list from the CSV file.
    
    Parameters:
    - file_name: The name of the CSV file that has the data
    """
    df = pd.read_csv(file_name)
    columns = df.columns.tolist()
    return str(columns)

@agent.tool
def query_liquidity_data(ctx: RunContext[None], 
                         query: str, 
                         output_file: str = "query_results.csv"):
    """
    Runs a GraphQL query on the given endpoint and saves the result to a CSV file.
    """
    # Set up transport and client
    transport = RequestsHTTPTransport(url=os.getenv("GRAPHQL_ENDPOINT"), verify=True, retries=3)
    client = Client(transport=transport, fetch_schema_from_transport=True)

    try:
        response = client.execute(gql(query))

        # Flatten the top-level field dynamically
        top_level_key = list(response.keys())[0]
        data = response[top_level_key]

        # Attempt flattening token subfields if they exist
        flat_data = []
        if len(data) > 0:
            for item in data:
                flat_item = item.copy()
                if "token" in item and isinstance(item["token"], dict):
                    flat_item.update({
                        "token_id": item["token"].get("id"),
                        "symbol": item["token"].get("symbol"),
                        "name": item["token"].get("name"),
                    })
                    del flat_item["token"]
                flat_data.append(flat_item)

            df = pd.DataFrame(flat_data)
            df.to_csv(output_file, index=False)
            print(f"Saved query results to {output_file}")
            return f"Saved query results to {output_file} \n dataset summary:\n {df.describe()}"

    except Exception as e:
        return f"GraphQL query failed: {response}"

@agent.tool()
def metric_calculator(ctx: RunContext[None], code: str):
    """
    Use this tool to run analysis code only in case you want to run calculations to get the final answer or a metric. Always use print statement to print the result in format 'The calculated value for <variable_name> is <calculated_value>'.
    Parameters:
    - code: The python code to execute to run calculations.
    """
    catcher = StringIO()
    try:    
        with redirect_stdout(catcher):
            exec(code)
        return catcher.getvalue()
    except Exception as e:
        return f"Failed to run code. Error: {repr(e)}"

@agent.tool()
def graph_generator(
    ctx: RunContext[None], 
    code: str
) -> str:
    """
    Use this tool to execute Python code.
    
    If you want to see the output of a value, you should use print statement 
    with `print(...)` function.
    
    NOTE: While plotting graph always sort the data in descending order 
    and take top 10 values and do not use show() function.
    """
    try:
        print('EXECUTING CODE')
        # Execute the code and capture output
        exec(code)
        print('CODE EXECUTED SUCCESSFULLY, MOVE ON TO NEXT STEP')
        
        # Return success message
        return (
            "Successfully executed the python code\n\n"
            "If you have completed all tasks, generate the final report and end the execution."
        )
        
    except Exception as e:
        return f"Failed to execute code. Error: {repr(e)}"

def run_agent(user_prompt: str):
    user_prompt = user_prompt
    deps = AgentState(user_query=user_prompt)
    result = agent.run_sync(user_prompt, deps=deps)

    return result.data 