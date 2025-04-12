# Crypto Pool Agent

A powerful agent for analyzing liquidity data from crypto pools using GraphQL queries, metric calculations, and data visualization.

## Features

- **GraphQL Query Tool**: Fetches liquidity data from subgraphs and saves results to CSV
- **Metric Calculator**: Computes key metrics from the data using Python code
- **Chart Generator**: Creates interactive visualizations using Plotly
- **PDF Report Generation**: Automatically generates comprehensive PDF reports
- **Command Line Interface**: Easy-to-use CLI for running analyses
- **Streamlit Dashboard**: Web interface for interactive analysis

## Prerequisites

- Python 3.8 or higher
- WSL (Windows Subsystem for Linux) with Ubuntu 22.04
- Access to a GraphQL endpoint for crypto pool data

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-pool-agent.git
cd crypto-pool-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your API keys and configuration:
```
OPENAI_API_KEY=your_openai_api_key
GRAPHQL_ENDPOINT=your_graphql_endpoint
LOGFIRE_TOKEN=your_logfire_token
```

## Usage

### Command Line Interface

Run an analysis with a specific query:

```bash
python src/main.py "Analyze the liquidity of Uniswap V3 pools"
```

The script will:
1. Query the subgraph for pool data
2. Calculate relevant metrics
3. Generate visualizations
4. Create a PDF report
5. Output paths to all generated files

### Python API

```python
from src.agent import run_agent

# Run analysis
result = run_agent("Analyze the liquidity of Uniswap V3 pools")

# Access results
print(f"PDF Report: {result.pdf_path}")
print(f"CSV Data: {result.csv_path}")
print(f"Metrics: {result.metrics_dict}")
```

## Application Flow

When a user submits a query through the Streamlit interface, the following sequence of operations occurs:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  User submits   │────▶│  streamlit_app.py│────▶│  get_agent_response() │
│     query       │     │  main()         │     │                 │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Display results│◀────│  run_agent()    │◀────│  agent.py       │
│  in UI          │     │                 │     │                 │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                        │
                                 ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │                 │     │                 │
                        │  tools/         │     │  tools/         │
                        │  subgraph_tool.py│────▶│  metric_tool.py │
                        │                 │     │                 │
                        └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  tools/         │
                                                │  chart_tool.py  │
                                                │                 │
                                                └─────────────────┘
```

### Detailed Flow Description:

1. **User Interaction**:
   - User enters a query in the Streamlit interface
   - The query is captured by `streamlit_app.py`

2. **Query Processing**:
   - `get_agent_response()` is called with the user's query
   - This function creates a new event loop and calls `run_agent()`

3. **Agent Execution**:
   - `run_agent()` in `agent.py` processes the query
   - It determines which tools to use based on the query
   - The agent execution follows this specific sequence:
     1. `run_agent()` in `agent.py` initializes the agent with the user's query
     2. `get_agent_system_prompt()` is called to generate the system prompt that defines the agent's capabilities and behavior
     3. The agent is initialized with this system prompt and the available tools
     4. The agent's `plan()` method analyzes the query and creates an execution plan
     5. The agent's `execute()` method runs the plan, which typically involves:
        - First calling `SubgraphQueryTool.run()` to fetch data from the GraphQL endpoint
        - Then calling `MetricCalculatorTool.run()` to process the fetched data
        - Finally calling `ChartGeneratorTool.run()` to create visualizations
     6. Each tool's `run()` method:
        - `SubgraphQueryTool.run()`: Executes GraphQL queries and saves results to CSV
        - `MetricCalculatorTool.run()`: Processes the CSV data and calculates metrics
        - `ChartGeneratorTool.run()`: Creates HTML and PNG visualizations from the metrics
     7. The agent's `format_response()` method combines all results into a structured response
     8. The response includes paths to generated files and a markdown report

4. **Tool Execution**:
   - `subgraph_tool.py` queries the GraphQL endpoint for pool data
   - `metric_tool.py` calculates metrics from the retrieved data
   - `chart_tool.py` generates visualizations from the metrics

5. **Result Generation**:
   - The agent combines results from all tools
   - Creates a markdown report with metrics and insights
   - Generates PDF and HTML visualizations

6. **UI Update**:
   - Results are returned to the Streamlit app
   - The UI displays the markdown report, metrics, and visualizations
   - User can download the PDF report

## Project Structure

```
crypto-pool-agent/
├── src/
│   ├── agent.py          # Core agent implementation
│   ├── main.py           # CLI entry point
│   ├── run.py            # Pipeline runner
│   ├── streamlit_app.py  # Streamlit web interface
│   └── tools/
│       ├── chart_tool.py    # Chart generation tool
│       ├── metric_tool.py   # Metric calculation tool
│       └── subgraph_tool.py # GraphQL query tool
├── output/               # Generated files
├── requirements.txt      # Project dependencies
├── pyproject.toml        # Project configuration
└── .env                 # Environment variables
```

## Tools

### Subgraph Query Tool
- Executes GraphQL queries against crypto pool subgraphs
- Automatically flattens nested data structures
- Saves results to CSV format

### Metric Calculator Tool
- Executes Python code to calculate metrics
- Supports pandas and numpy operations
- Returns formatted results

### Chart Generator Tool
- Creates interactive Plotly visualizations
- Supports multiple chart types
- Exports to HTML and PNG formats

## Output Files

- **PDF Report**: Comprehensive analysis with metrics and insights
- **CSV Data**: Raw data from the subgraph query
- **HTML Charts**: Interactive visualizations
- **PNG Charts**: Static chart images
- **Metrics**: Calculated metrics in tabular format

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Portia](https://github.com/portia-ai/portia)
- Uses [LangChain](https://github.com/langchain-ai/langchain) for agent capabilities
- Powered by [OpenAI](https://openai.com/) GPT-4 