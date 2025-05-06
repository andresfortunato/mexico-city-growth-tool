# Mexico City Growth Diagnostics Dashboard

This dashboard visualizes growth diagnostics data for Mexican cities, focusing on employment, wages, population growth, and housing costs.

## Features

The dashboard includes 8 visualizations:
1. Employment rate vs. population by city
2. Population growth boxplots by year
3. Scatter plot of population growth vs. real wages
4. CAGR of real wages vs. population growth
5. CAGR of nominal wages vs. migration/population growth
6. Line graph of nominal wages over time
7. Line graph of real wages over time
8. Line graph of housing costs

## Installation

1. Install Python 3.9+ if not already installed.
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the dashboard:

```bash
python mexico_city_dashboard.py
```

2. Open a web browser and navigate to:
```
http://127.0.0.1:8050/
```

3. Use the dropdown menu to select a city for analysis.

## Data Sources

The dashboard uses the following data files:
- Employment rate by city.xls
- Mean hourly salary by city.xls
- Population by city.xls
- Indice SHF datos abiertos 4_trim_2024(Indice SHF datos abiertos).csv

If any of these files are missing, the dashboard will use sample data instead.

## Notes

- Monthly nominal salary is calculated as hourly salary × 160 hours
- Real wages are calculated as monthly salary divided by the housing cost index
- CAGR values are calculated for the period 2015-2020

## Individual Graph Files

When you run the dashboard, it will also generate individual HTML files for each graph (8 in total), which can be opened directly in any web browser without running the server. 