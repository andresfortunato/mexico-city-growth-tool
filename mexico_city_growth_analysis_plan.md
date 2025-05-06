# Mexico City Growth Diagnostics Analysis Plan

Based on the available data, we need to compile a cohesive dataset and create seven key visualizations that will help analyze city growth patterns in Mexico.

## Data Sources
The following data sources are available:
1. **Employment rate by city** - Excel file with employment rates by quarter/year
2. **Mean hourly salary by city** - Excel file with hourly wages by quarter/year
3. **Population by city** - Excel file with population data by quarter/year
4. **Housing costs** - SHF-CONAVI House-Price Index in CSV format

## Data Processing Steps

### 1. Data Compilation
First, we need to compile all data into a single unified dataset with the following columns:
- City
- Year
- Quarter
- Time point (YYYYQN format)
- Employment rate
- Hourly salary
- Monthly salary (= hourly salary * 160 hours)
- Population
- Housing index
- Real wage (= monthly salary / housing index)

### 2. Calculate Growth Rates and Metrics
Once we have the unified dataset, we need to calculate:
- Year-over-year growth rates for population, nominal wages, and real wages
- Compound Annual Growth Rates (CAGR) for specific time periods
- Annual averages for each metric

## Visualizations to Create

### 1. Employment Rate vs. Population by City (Levels)
- Scatter plot with all cities
- Population on x-axis, employment rate on y-axis
- Highlight selected city
- Allow selection of time period (start year to end year)

### 2. Population Growth Boxplots
- Boxplots of population growth rates by year
- Red dot highlighting the selected city
- Compare growth of the selected city against the distribution of all cities

### 3. Population Growth vs. Real Wages Scatter Plot
- Scatter plot with all cities
- Population growth on x-axis, real wages on y-axis
- Highlight selected city
- Allow selection of time period (start year to end year)

### 4. CAGR Real Wages vs. Population Growth
- Scatter plot with all cities
- CAGR of real wages on x-axis, population growth on y-axis
- Highlight selected city
- Allow selection of time period (start year to end year)

### 5. CAGR Nominal Wages vs. Population Growth
- Scatter plot with all cities
- CAGR of nominal wages on x-axis, population growth or net migration on y-axis
- Highlight selected city
- Allow selection of time period (start year to end year)

### 6. Nominal Wages by Year (Line Graph)
- Line graph showing nominal wages over time for selected city
- Second line showing median nominal wages for all cities
- Allow selection of time period

### 7. Real Wages by Year (Line Graph)
- Line graph showing real wages over time for selected city
- Second line showing median real wages for all cities
- Allow selection of time period

### 8. Housing Costs by Year (Line Graph)
- Line graph showing housing cost index over time for selected city
- Second line showing median housing cost index for all cities
- Allow selection of time period

## Implementation Approach

1. **Python with pandas** for data processing:
   - Read and clean the Excel and CSV data
   - Join all data sources
   - Calculate monthly salaries and real wages
   - Calculate growth rates and CAGR

2. **Visualization options**:
   - **Plotly** for interactive visualizations
   - **Matplotlib/Seaborn** for static visualizations
   - Consider creating a simple dashboard with **Streamlit** or **Dash**

3. **Technical Considerations**:
   - When reading Excel files, handle proper parsing of HTML content
   - Match city names across different data sources
   - Handle missing values and outliers
   - Standardize time periods across all datasets

## Calculations

1. **Monthly nominal salary**:
   - Hourly salary × 160 hours per month

2. **Real wages**:
   - Monthly nominal salary ÷ Housing cost index

3. **Year-over-year growth rate**:
   - (Current year value ÷ Previous year value - 1) × 100%

4. **Compound Annual Growth Rate (CAGR)**:
   - (End value ÷ Start value)^(1/number of years) - 1

## Notes on Data Analysis

1. For the analysis, we need to use real wages (nominal wages adjusted for housing costs) to understand the effective purchasing power of workers in different cities.

2. Comparing population growth with wage growth helps identify if a city is attracting people despite low wages (indicating non-wage amenities) or losing people despite high wages (indicating housing constraints or other issues).

3. The relationship between population growth and employment rates helps identify labor market health.

4. Time series analysis of wages and housing costs helps identify trends and potential constraints to growth. 