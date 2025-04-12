# Pool-Sweeper: AI-Powered Liquidity Analysis

![Pool-Sweeper Logo](assets/logo.png)

## Overview

Pool-Sweeper is an advanced AI-powered tool designed for comprehensive liquidity analysis. It provides an interactive interface for users to analyze and understand liquidity pools through natural language queries.

## Features

- 🤖 **AI-Powered Analysis**: Utilizes advanced AI to process and analyze liquidity data
- 💬 **Natural Language Interface**: Ask questions in plain English about your liquidity data
- 📊 **Interactive Visualizations**: Dynamic charts and graphs for data visualization
- 📑 **PDF Report Generation**: Generate detailed PDF reports of your analysis
- 🎨 **Modern UI/UX**: Clean, intuitive interface with a responsive design
- 🔄 **Real-time Processing**: Get instant responses to your queries

## Installation

### Prerequisites

- Python 3.9+
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/kumarvipu1/crypto-pool-agent/tree/main
cd crypto-pool-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. create a .env file and add the following:
```bash
OPENAI_API_KEY=your_openai_api_key
```

4. Run the application:
```bash
streamlit run chat_interface.py
```

## Usage

1. Launch the application using the command above
2. Enter your query in the chat input at the bottom of the screen
3. View the analysis results, including:
   - Detailed markdown reports
   - Interactive visualizations
   - Downloadable PDF reports

## Project Structure

```
crypto-pool-agent/
├── assets/             # Static assets (images, logos)
├── chat_interface.py   # Main Streamlit interface
├── agent_module.py     # AI agent implementation
├── requirements.txt    # Dependencies
└── README.md          # Project documentation
```

## Features in Detail

### AI Analysis
- Natural language processing for query understanding
- Comprehensive liquidity pool analysis
- Pattern recognition in trading data

### Visualization
- Interactive charts and graphs
- Real-time data updates
- Custom visualization options

### Reporting
- Automated PDF report generation
- Customizable report templates
- Export functionality for further analysis


*Note: This project is for demonstration purposes. Please ensure you have the necessary permissions and comply with relevant regulations when analyzing financial data.* 