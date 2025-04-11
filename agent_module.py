
from langchain_experimental.utilities import PythonREPL
from typing import Annotated, List, Optional, Tuple, Union, Dict, Any
from pydantic import BaseModel, Field
import re
import dotenv
from pydantic_ai import Agent, RunContext, ModelRetry
from dataclasses import dataclass
from markdown_pdf import MarkdownPdf, Section
from pydantic_ai.models import openai
import dotenv
from pinecone import Pinecone
import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
import os
from pydantic_ai.models import ModelSettings
from openai import OpenAI
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from datetime import datetime
import logfire
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
from datetime import datetime
import json

dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("agusto-demo")




logfire.configure(token=os.getenv("LOGFIRE_TOKEN"), scrubbing=False)


def read_json_file(filepath: str) -> Union[str, Dict[str, Any]]:
    """
    Reads a JSON file and returns its contents as a dictionary string.
    
    Args:
        filepath (str): Path to the JSON file
        
    Returns:
        Union[str, Dict[str, Any]]: JSON content as a formatted string or dictionary
                                   Error message string if file reading fails
        
    Example:
        >>> content = read_json_file("config.json")
        >>> print(content)
        {
            "name": "John",
            "age": 30,
            "city": "New York"
        }
    """
    try:
        # Convert string path to Path object
        file_path = Path(filepath)
        
        # Check if file exists and has .json extension
        if not file_path.is_file():
            return f"Error: File not found at {filepath}"
        
        if file_path.suffix.lower() != '.json':
            return f"Error: File {filepath} is not a JSON file"
            
        # Read and parse JSON file
        with file_path.open('r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            # Return formatted JSON string with indentation
            return json.dumps(data, indent=4)
            
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON format in file - {str(e)}"
    except Exception as e:
        return f"Error reading file: {str(e)}"
    

schema = """
type Factory @entity {
  # factory address
  id: ID!
  # amount of pools created
  poolCount: BigInt!
  # amoutn of transactions all time
  txCount: BigInt!
  # total volume all time in derived USD
  totalVolumeUSD: BigDecimal!
  # total volume all time in derived ETH
  totalVolumeETH: BigDecimal!
  # total swap fees all time in USD
  totalFeesUSD: BigDecimal!
  # total swap fees all time in USD
  totalFeesETH: BigDecimal!
  # all volume even through less reliable USD values
  untrackedVolumeUSD: BigDecimal!
  # TVL derived in USD
  totalValueLockedUSD: BigDecimal!
  # TVL derived in ETH
  totalValueLockedETH: BigDecimal!
  # TVL derived in USD untracked
  totalValueLockedUSDUntracked: BigDecimal!
  # TVL derived in ETH untracked
  totalValueLockedETHUntracked: BigDecimal!

  # current owner of the factory
  owner: ID!
}

# stores for USD calculations
type Bundle @entity {
  id: ID!
  # price of ETH in usd
  ethPriceUSD: BigDecimal!
}

type Token @entity {
  # token address
  id: Bytes!
  # token symbol
  symbol: String!
  # token name
  name: String!
  # token decimals
  decimals: BigInt!
  # token total supply
  totalSupply: BigInt!
  # volume in token units
  volume: BigDecimal!
  # volume in derived USD
  volumeUSD: BigDecimal!
  # volume in USD even on pools with less reliable USD values
  untrackedVolumeUSD: BigDecimal!
  # fees in USD
  feesUSD: BigDecimal!
  # transactions across all pools that include this token
  txCount: BigInt!
  # number of pools containing this token
  poolCount: BigInt!
  # liquidity across all pools in token units
  totalValueLocked: BigDecimal!
  # liquidity across all pools in derived USD
  totalValueLockedUSD: BigDecimal!
  # TVL derived in USD untracked
  totalValueLockedUSDUntracked: BigDecimal!
  # Note: for chains where ETH is not the native token, this will be the derived
  # price of that chain's native token, effectively, this should be renamed
  # derivedNative
  derivedETH: BigDecimal!
  # pools token is in that are white listed for USD pricing
  whitelistPools: [Pool!]!
  # derived fields
  tokenDayData: [TokenDayData!]! @derivedFrom(field: "token")
}

type Pool @entity {
  # pool address
  id: Bytes!
  # creation
  createdAtTimestamp: BigInt!
  # block pool was created at
  createdAtBlockNumber: BigInt!
  # token0
  token0: Token!
  # token1
  token1: Token!
  # fee amount
  feeTier: BigInt!
  # in range liquidity
  liquidity: BigInt!
  # current price tracker
  sqrtPrice: BigInt!
  # token0 per token1
  token0Price: BigDecimal!
  # token1 per token0
  token1Price: BigDecimal!
  # current tick
  tick: BigInt
  # current observation index
  observationIndex: BigInt!
  # all time token0 swapped
  volumeToken0: BigDecimal!
  # all time token1 swapped
  volumeToken1: BigDecimal!
  # all time USD swapped
  volumeUSD: BigDecimal!
  # all time USD swapped, unfiltered for unreliable USD pools
  untrackedVolumeUSD: BigDecimal!
  # fees in USD
  feesUSD: BigDecimal!
  # all time number of transactions
  txCount: BigInt!
  # all time fees collected token0
  collectedFeesToken0: BigDecimal!
  # all time fees collected token1
  collectedFeesToken1: BigDecimal!
  # all time fees collected derived USD
  collectedFeesUSD: BigDecimal!
  # total token 0 across all ticks
  totalValueLockedToken0: BigDecimal!
  # total token 1 across all ticks
  totalValueLockedToken1: BigDecimal!
  # tvl derived ETH
  totalValueLockedETH: BigDecimal!
  # tvl USD
  totalValueLockedUSD: BigDecimal!
  # TVL derived in USD untracked
  totalValueLockedUSDUntracked: BigDecimal!
  # Fields used to help derived relationship
  liquidityProviderCount: BigInt! # used to detect new exchanges
  # hourly snapshots of pool data
  poolHourData: [PoolHourData!]! @derivedFrom(field: "pool")
  # daily snapshots of pool data
  poolDayData: [PoolDayData!]! @derivedFrom(field: "pool")
  # derived fields
  mints: [Mint!]! @derivedFrom(field: "pool")
  burns: [Burn!]! @derivedFrom(field: "pool")
  swaps: [Swap!]! @derivedFrom(field: "pool")
  collects: [Collect!]! @derivedFrom(field: "pool")
  ticks: [Tick!]! @derivedFrom(field: "pool")
}

type Tick @entity {
  # format: <pool address>#<tick index>
  id: ID!
  # pool address
  poolAddress: Bytes!
  # tick index
  tickIdx: BigInt!
  # pointer to pool
  pool: Pool!
  # total liquidity pool has as tick lower or upper
  liquidityGross: BigInt!
  # how much liquidity changes when tick crossed
  liquidityNet: BigInt!
  # calculated price of token0 of tick within this pool - constant
  price0: BigDecimal!
  # calculated price of token1 of tick within this pool - constant
  price1: BigDecimal!
  # created time
  createdAtTimestamp: BigInt!
  # created block
  createdAtBlockNumber: BigInt!
}

type Transaction @entity {
  # txn hash
  id: ID!
  # block txn was included in
  blockNumber: BigInt!
  # timestamp txn was confirmed
  timestamp: BigInt!
  # gas used during txn execution
  gasUsed: BigInt!
  gasPrice: BigInt!
  # derived values
  mints: [Mint]! @derivedFrom(field: "transaction")
  burns: [Burn]! @derivedFrom(field: "transaction")
  swaps: [Swap]! @derivedFrom(field: "transaction")
  flashed: [Flash]! @derivedFrom(field: "transaction")
  collects: [Collect]! @derivedFrom(field: "transaction")
}

type Mint @entity {
  # transaction hash + "#" + index in mints Transaction array
  id: ID!
  # which txn the mint was included in
  transaction: Transaction!
  # time of txn
  timestamp: BigInt!
  # pool position is within
  pool: Pool!
  # allow indexing by tokens
  token0: Token!
  # allow indexing by tokens
  token1: Token!
  # owner of position where liquidity minted to
  owner: Bytes!
  # the address that minted the liquidity
  sender: Bytes
  # txn origin
  origin: Bytes! # the EOA that initiated the txn
  # amount of liquidity minted
  amount: BigInt!
  # amount of token 0 minted
  amount0: BigDecimal!
  # amount of token 1 minted
  amount1: BigDecimal!
  # derived amount based on available prices of tokens
  amountUSD: BigDecimal
  # lower tick of the position
  tickLower: BigInt!
  # upper tick of the position
  tickUpper: BigInt!
  # order within the txn
  logIndex: BigInt
}

type Burn @entity {
  # transaction hash + "#" + index in mints Transaction array
  id: ID!
  # txn burn was included in
  transaction: Transaction!
  # pool position is within
  pool: Pool!
  # allow indexing by tokens
  token0: Token!
  # allow indexing by tokens
  token1: Token!
  # need this to pull recent txns for specific token or pool
  timestamp: BigInt!
  # owner of position where liquidity was burned
  owner: Bytes
  # txn origin
  origin: Bytes! # the EOA that initiated the txn
  # amouny of liquidity burned
  amount: BigInt!
  # amount of token 0 burned
  amount0: BigDecimal!
  # amount of token 1 burned
  amount1: BigDecimal!
  # derived amount based on available prices of tokens
  amountUSD: BigDecimal
  # lower tick of position
  tickLower: BigInt!
  # upper tick of position
  tickUpper: BigInt!
  # position within the transactions
  logIndex: BigInt
}

type Swap @entity {
  # transaction hash + "#" + index in swaps Transaction array
  id: ID!
  # pointer to transaction
  transaction: Transaction!
  # timestamp of transaction
  timestamp: BigInt!
  # pool swap occured within
  pool: Pool!
  # allow indexing by tokens
  token0: Token!
  # allow indexing by tokens
  token1: Token!
  # sender of the swap
  sender: Bytes!
  # recipient of the swap
  recipient: Bytes!
  # txn origin
  origin: Bytes! # the EOA that initiated the txn
  # delta of token0 swapped
  amount0: BigDecimal!
  # delta of token1 swapped
  amount1: BigDecimal!
  # derived info
  amountUSD: BigDecimal!
  # The sqrt(price) of the pool after the swap, as a Q64.96
  sqrtPriceX96: BigInt!
  # the tick after the swap
  tick: BigInt!
  # index within the txn
  logIndex: BigInt
}

type Collect @entity {
  # transaction hash + "#" + index in collect Transaction array
  id: ID!
  # pointer to txn
  transaction: Transaction!
  # timestamp of event
  timestamp: BigInt!
  # pool collect occured within
  pool: Pool!
  # owner of position collect was performed on
  owner: Bytes
  # amount of token0 collected
  amount0: BigDecimal!
  # amount of token1 collected
  amount1: BigDecimal!
  # derived amount based on available prices of tokens
  amountUSD: BigDecimal
  # lower tick of position
  tickLower: BigInt!
  # uppper tick of position
  tickUpper: BigInt!
  # index within the txn
  logIndex: BigInt
}

type Flash @entity {
  # transaction hash + "-" + index in collect Transaction array
  id: ID!
  # pointer to txn
  transaction: Transaction!
  # timestamp of event
  timestamp: BigInt!
  # pool collect occured within
  pool: Pool!
  # sender of the flash
  sender: Bytes!
  # recipient of the flash
  recipient: Bytes!
  # amount of token0 flashed
  amount0: BigDecimal!
  # amount of token1 flashed
  amount1: BigDecimal!
  # derived amount based on available prices of tokens
  amountUSD: BigDecimal!
  # amount token0 paid for flash
  amount0Paid: BigDecimal!
  # amount token1 paid for flash
  amount1Paid: BigDecimal!
  # index within the txn
  logIndex: BigInt
}

# Data accumulated and condensed into day stats for all of Uniswap
type UniswapDayData @entity {
  # timestamp rounded to current day by dividing by 86400
  id: ID!
  # timestamp rounded to current day by dividing by 86400
  date: Int!
  # total daily volume in Uniswap derived in terms of ETH
  volumeETH: BigDecimal!
  # total daily volume in Uniswap derived in terms of USD
  volumeUSD: BigDecimal!
  # total daily volume in Uniswap derived in terms of USD untracked
  volumeUSDUntracked: BigDecimal!
  # fees in USD
  feesUSD: BigDecimal!
  # number of daily transactions
  txCount: BigInt!
  # tvl in terms of USD
  tvlUSD: BigDecimal!
}

# Data accumulated and condensed into day stats for each pool
type PoolDayData @entity {
  # timestamp rounded to current day by dividing by 86400
  id: ID!
  # timestamp rounded to current day by dividing by 86400
  date: Int!
  # pointer to pool
  pool: Pool!
  # in range liquidity at end of period
  liquidity: BigInt!
  # current price tracker at end of period
  sqrtPrice: BigInt!
  # price of token0 - derived from sqrtPrice
  token0Price: BigDecimal!
  # price of token1 - derived from sqrtPrice
  token1Price: BigDecimal!
  # current tick at end of period
  tick: BigInt
  # tvl derived in USD at end of period
  tvlUSD: BigDecimal!
  # volume in token0
  volumeToken0: BigDecimal!
  # volume in token1
  volumeToken1: BigDecimal!
  # volume in USD
  volumeUSD: BigDecimal!
  # fees in USD
  feesUSD: BigDecimal!
  # numebr of transactions during period
  txCount: BigInt!
  # opening price of token0
  open: BigDecimal!
  # high price of token0
  high: BigDecimal!
  # low price of token0
  low: BigDecimal!
  # close price of token0
  close: BigDecimal!
}

# hourly stats tracker for pool
type PoolHourData @entity {
  # format: <pool address>-<timestamp>
  id: ID!
  # unix timestamp for start of hour
  periodStartUnix: Int!
  # pointer to pool
  pool: Pool!
  # in range liquidity at end of period
  liquidity: BigInt!
  # current price tracker at end of period
  sqrtPrice: BigInt!
  # price of token0 - derived from sqrtPrice
  token0Price: BigDecimal!
  # price of token1 - derived from sqrtPrice
  token1Price: BigDecimal!
  # current tick at end of period
  tick: BigInt
  # tvl derived in USD at end of period
  tvlUSD: BigDecimal!
  # volume in token0
  volumeToken0: BigDecimal!
  # volume in token1
  volumeToken1: BigDecimal!
  # volume in USD
  volumeUSD: BigDecimal!
  # fees in USD
  feesUSD: BigDecimal!
  # numebr of transactions during period
  txCount: BigInt!
  # opening price of token0
  open: BigDecimal!
  # high price of token0
  high: BigDecimal!
  # low price of token0
  low: BigDecimal!
  # close price of token0
  close: BigDecimal!
}

type TokenDayData @entity {
  # token address concatendated with date
  id: ID!
  # timestamp rounded to current day by dividing by 86400
  date: Int!
  # pointer to token
  token: Token!
  # volume in token units
  volume: BigDecimal!
  # volume in derived USD
  volumeUSD: BigDecimal!
  # volume in USD even on pools with less reliable USD values
  untrackedVolumeUSD: BigDecimal!
  # liquidity across all pools in token units
  totalValueLocked: BigDecimal!
  # liquidity across all pools in derived USD
  totalValueLockedUSD: BigDecimal!
  # price at end of period in USD
  priceUSD: BigDecimal!
  # fees in USD
  feesUSD: BigDecimal!
  # opening price USD
  open: BigDecimal!
  # high price USD
  high: BigDecimal!
  # low price USD
  low: BigDecimal!
  # close price USD
  close: BigDecimal!
}

type TokenHourData @entity {
  # token address concatendated with date
  id: ID!
  # unix timestamp for start of hour
  periodStartUnix: Int!
  # pointer to token
  token: Token!
  # volume in token units
  volume: BigDecimal!
  # volume in derived USD
  volumeUSD: BigDecimal!
  # volume in USD even on pools with less reliable USD values
  untrackedVolumeUSD: BigDecimal!
  # liquidity across all pools in token units
  totalValueLocked: BigDecimal!
  # liquidity across all pools in derived USD
  totalValueLockedUSD: BigDecimal!
  # price at end of period in USD
  priceUSD: BigDecimal!
  # fees in USD
  feesUSD: BigDecimal!
  # opening price USD
  open: BigDecimal!
  # high price USD
  high: BigDecimal!
  # low price USD
  low: BigDecimal!
  # close price USD
  close: BigDecimal!
}
"""





@dataclass
class agent_state:
    user_query: str = Field(description="The user quer that needs to be answered")



# Output structure
class agent_response(BaseModel):
    markdown_report: str = Field(description="The markdown report of the user query")
    csv_path: str = Field(description="The path where the reference csv file is stored as retreived by the tool")
    metrics_dict: str = Field(description = "A string of metrics calculated from the data in tabular format using tabulate library as returned by the metric_calculator tool")
    html_path: str = Field(description = "The path where the html of visualizations is stored")
    png_path: str = Field(description = "The path where the png of visualizations is stored")
    pdf_path: str = Field(description = "The path where the pdf of the report can be stored")
    
model = openai.OpenAIModel('gpt-4o', api_key=os.getenv('OPENAI_API_KEY'))
agent = Agent(model=model, deps_type=agent_state, result_type=agent_response)

current_date = datetime.now().strftime("%Y-%m-%d")

@agent.system_prompt
def get_agent_system_prompt(ctx: RunContext[agent_state]):
    
    prompt = f"""
    You are an analyst for a a crypto trading company. Your goal is to analyse liquidity of a crypto token and provide users important information relevant to the user query with a detailed report.
    The user will provide you a query and schema of the liquidity information of the crypto token. You will access the relevant to the tools help you to retreive the liquidity information of the crypto token.
    The user query is:\n {ctx.deps.user_query} and the current date is {current_date}\n
    The graphql schema of the liquidity information of the crypto token is:
    {schema}
    
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
    file_name: Annotated[str, "The name of the csv file that has the data"]
):
    """
    Use this tool to get the column list from the CSV file.
    
    Parameters:
    - file_name: The name of the CSV file that has the data
    """
    df = pd.read_csv(file_name)
    columns = df.columns.tolist()
    return str(columns)


# Fetch paginated data
@agent.tool
def query_liquidity_data(ctx: RunContext[None], 
                         query: Annotated[str, "The GraphQL query to fetch the data"], 
                         output_file: Annotated[str, "The name of the csv file that has the data"] = "query_results.csv"):
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

'''
@agent.tool
def write_markdown_to_file(ctx: RunContext[None], content: Annotated[str, "The markdown content to write"], 
                        filename: Annotated[str, "The name of the file (with or without .md extension)"] = "blog.md") -> str:
    """
    Write markdown content to a file with .md extension.
    Parameters:
    - content: The markdown content to write.
    - filename: The name of the file (with or without .md extension).
    """
    # Ensure filename has .md extension
    if not filename.endswith('.md'):
        filename += '.md'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
        
    pdf = MarkdownPdf()
    pdf.add_section(Section(content, toc=False))
    pdf.save(filename.replace('.md', '.pdf'))
        
    return f"File {filename} has been created successfully."
'''



@agent.tool()
def metric_calculator(ctx: RunContext[None], code: Annotated[str, "The python code to execute to run calculations"]):
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
    code: Annotated[str, "The python code to execute to generate your chart."]
) -> str:
    """
    Use this tool to execute Python code.
    
    If you want to see the output of a value, you should use print statement 
    with `print(...)` function.
    
    NOTE: While plotting graph always sort the data in descending order 
    and take top 10 values and do not use show() function.
    """
    repl = PythonREPL()
    
    try:
        print('EXECUTING CODE')
        # Execute the code and capture output
        output = repl.run(code)
        print('CODE EXECUTED SUCCESSFULLY, MOVE ON TO NEXT STEP')
        
        # Check for errors in output
        if 'Error' in str(output):
            return (
                f"Failed to execute code. Error:\n"
                f"{output}\n\n"
                "Please review the code and try again"
            )
        
        # Return success message
        return (
            "Successfully executed the python code\n\n"
            "If you have completed all tasks, generate the final report and end the execution."
        )
        
    except Exception as e:
        return f"Failed to execute code. Error: {repr(e)}"
    

# Running the agent
def run_agent(user_prompt: str):
    user_prompt = user_prompt
    deps = agent_state(user_query=user_prompt)
    result = agent.run_sync(user_prompt, deps=deps, model_settings=ModelSettings(temperature=0.5, timeout=100))

    return result.data

    
