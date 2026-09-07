# Lab Activity 7: Data Mining APIs and Interactive Data Visualization

**Student:** BRAEDEN JOSH V. PILARO  
**Course:** CPE106L-4 Software Design Laboratory  
**Laboratory Activity:** Lab Activity 7

## Project Description

This project retrieves life expectancy data from the World Bank
Indicators API. It processes the returned JSON records using Pandas,
calculates descriptive statistics, and creates an interactive Plotly
line chart.

## Data Source

- Source: World Bank Indicators API
- Indicator: SP.DYN.LE00.IN
- Indicator name: Life expectancy at birth, total (years)
- API base address: https://api.worldbank.org/v2/

No API key is required.

## Countries Included

- Philippines
- Indonesia
- Malaysia
- Thailand
- Vietnam
- Singapore

## Project Structure

pilaro_braedenjosh_labactivity7/
- src/ - Python source code
- data/ - Processed CSV datasets
- outputs/ - Interactive charts and summaries
- tests/ - Automated Python tests
- screenshots/ - Terminal and visualization evidence

## Environment Setup

Create the Conda environment:

```bash
conda env create -f environment.yml