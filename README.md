# Crypto Pool Agent

A Streamlit-based application for analyzing crypto liquidity pools using GraphQL queries and data visualization.

## Project Structure

```
.
├── src/
│   ├── tools/              # Tool implementations
│   │   ├── subgraph_tool.py    # GraphQL query tool
│   │   ├── metric_tool.py      # Metric calculation tool
│   │   └── chart_tool.py       # Chart generation tool
│   ├── main.py            # Main application entry point
│   ├── streamlit_app.py   # Streamlit interface
│   └── requirements.txt    # Python dependencies
├── assets/                # Static assets
├── .env                   # Environment variables
└── .gitignore            # Git ignore rules
```

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
cd src
pip install -r requirements.txt
```

3. Configure environment variables:
- Copy `.env.example` to `.env`
- Update the variables in `.env` with your values

## Running the Application

```bash
cd src
streamlit run streamlit_app.py
```

## Features

- GraphQL query execution for crypto pool data
- Metric calculation and analysis
- Interactive chart generation
- Streamlit-based user interface

## Tools

1. **SubgraphQueryTool**: Executes GraphQL queries and saves results to CSV
2. **MetricCalculatorTool**: Calculates metrics from CSV data
3. **ChartGeneratorTool**: Generates visualizations from data

## License

MIT License 