#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mexico City Growth Diagnostics Dashboard
This script generates a dashboard with 8 visualizations for a selected Mexican city:
1. Employment rate vs. population by city
2. Population growth boxplots by year
3. Scatter plot of population growth vs. real wages
4. CAGR of real wages vs. population growth
5. CAGR of nominal wages vs. migration/population growth
6. Line graph of nominal wages over time
7. Line graph of real wages over time
8. Line graph of housing costs
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from bs4 import BeautifulSoup
import re
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Define paths to data files
employment_rate_file = "Employment rate by city.xls"
hourly_salary_file = "Mean hourly salary by city.xls" 
population_file = "Population by city.xls"
housing_cost_file = "Indice SHF datos abiertos 4_trim_2024(Indice SHF datos abiertos).csv"

# Functions to read and clean data
def read_excel_html_table(file_path):
    """Read HTML tables stored in .xls format and extract city data."""
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    rows = soup.find_all('tr')
    
    # Extract years and quarters from header rows
    header_row = rows[6]  # Zero-indexed, so 7th row
    years = [th.text.strip() for th in header_row.find_all('td')[1:]]
    
    quarter_row = rows[7]  # 8th row
    quarters = [td.text.strip() for td in quarter_row.find_all('td')[1:]]
    
    # Create time points
    time_points = []
    for i in range(len(years)):
        if years[i] and quarters[i]:
            time_points.append(f"{years[i]}Q{quarters[i].split()[0]}")
    
    # Extract data for each city
    city_data = {}
    for row in rows[8:]:  # Start from 9th row
        cells = row.find_all('td')
        if len(cells) > 1:
            city_name = cells[0].text.strip()
            if city_name and city_name != "Áreas metropolitanas":
                values = []
                for cell in cells[1:]:
                    text = cell.text.strip()
                    if text == "No aplica":
                        values.append(np.nan)
                    else:
                        try:
                            values.append(float(text.replace(',', '.')))
                        except (ValueError, TypeError):
                            values.append(np.nan)
                
                # Create a Series with time points as index
                if len(values) == len(time_points):
                    city_data[city_name] = pd.Series(values, index=time_points)
    
    return city_data, time_points

def read_housing_cost(file_path):
    """Read housing cost data from CSV file."""
    # Read CSV file with semicolon separator
    data = pd.read_csv(file_path, sep=';', encoding='latin-1')
    
    # Filter for ZM (zona metropolitana) entries
    zm_data = data[data['Global'].str.contains('^ZM', regex=True)]
    
    # Create a lookup from city name to index values
    result = {}
    zm_names = zm_data['Global'].unique()
    
    for zm in zm_names:
        city_name = zm.replace('ZM ', '')
        if city_name == 'Valle México':
            city_name = 'Ciudad de México'
        if city_name == 'PueblaTlax':
            city_name = 'Ciudad de Puebla'
        
        # Get all rows for this ZM
        zm_rows = zm_data[zm_data['Global'] == zm]
        
        # Create time series
        years = zm_rows['Año'].astype(str)
        quarters = zm_rows['Trimestre'].astype(str)
        time_points = years + 'Q' + quarters
        values = zm_rows['Indice'].values
        
        result[city_name] = pd.Series(values, index=time_points)
    
    return result

# Process data
try:
    print("Reading employment data...")
    employment_data, time_points = read_excel_html_table(employment_rate_file)
    print("Reading salary data...")
    salary_data, _ = read_excel_html_table(hourly_salary_file)
    print("Reading population data...")
    population_data, _ = read_excel_html_table(population_file)
    print("Reading housing cost data...")
    housing_cost_data = read_housing_cost(housing_cost_file)
except Exception as e:
    print(f"Error reading data: {str(e)}")
    # If we can't read the actual data, use sample data instead
    from mexico_city_sample import generate_sample_data
    city_data_df = generate_sample_data()
    print("Using sample data instead.")
    has_real_data = False
else:
    has_real_data = True

# Compile data if real data is available
def compile_data(employment_data, salary_data, population_data, housing_cost_data, time_points):
    """Compile data into a single DataFrame."""
    # Get all city names
    all_cities = set(list(employment_data.keys()) + list(salary_data.keys()) + list(population_data.keys()))
    
    # Initialize result dataframe
    result_data = []
    
    for city in all_cities:
        if city == "Áreas metropolitanas" or not city:
            continue
        
        # Parse time points to get year and quarter
        for tp in time_points:
            match = re.match(r'(\d{4})Q(\d)', tp)
            if match:
                year = int(match.group(1))
                quarter = int(match.group(2))
                
                # Get data for this city and time point
                emp_value = employment_data.get(city, pd.Series()).get(tp, np.nan)
                salary_value = salary_data.get(city, pd.Series()).get(tp, np.nan)
                pop_value = population_data.get(city, pd.Series()).get(tp, np.nan)
                
                # Find matching housing cost data
                index_value = np.nan
                city_simple_name = city.replace('Ciudad de ', '')
                if city_simple_name in housing_cost_data:
                    housing_series = housing_cost_data[city_simple_name]
                    index_value = housing_series.get(tp, np.nan)
                elif city in housing_cost_data:
                    housing_series = housing_cost_data[city]
                    index_value = housing_series.get(tp, np.nan)
                
                # Calculate monthly salary (hourly salary * 160 hours)
                monthly_salary = salary_value * 160 if not np.isnan(salary_value) else np.nan
                
                # Calculate real wages (monthly salary / housing cost index)
                real_wage = monthly_salary / index_value if not np.isnan(monthly_salary) and not np.isnan(index_value) else np.nan
                
                # Add to result
                result_data.append({
                    'city': city,
                    'time_point': tp,
                    'year': year,
                    'quarter': quarter,
                    'employment_rate': emp_value,
                    'hourly_salary': salary_value,
                    'population': pop_value,
                    'housing_index': index_value,
                    'monthly_salary': monthly_salary,
                    'real_wage': real_wage
                })
    
    return pd.DataFrame(result_data)

if has_real_data:
    # Compile the data
    print("Compiling data...")
    city_data_df = compile_data(employment_data, salary_data, population_data, housing_cost_data, time_points)

# Calculate yearly averages and growth rates
def calculate_growth_rates(data):
    """Calculate year-over-year growth rates."""
    # Group by city and year, taking the average for each year
    yearly_data = data.groupby(['city', 'year']).agg({
        'employment_rate': 'mean',
        'monthly_salary': 'mean',
        'real_wage': 'mean',
        'population': 'mean',
        'housing_index': 'mean'
    }).reset_index()
    
    # Calculate year-over-year growth rates
    yearly_growth = []
    
    for city in yearly_data['city'].unique():
        city_data = yearly_data[yearly_data['city'] == city].sort_values('year')
        
        for i in range(1, len(city_data)):
            prev_year = city_data.iloc[i-1]
            curr_year = city_data.iloc[i]
            
            population_growth = ((curr_year['population'] / prev_year['population']) - 1) * 100 if not np.isnan(prev_year['population']) and prev_year['population'] > 0 else np.nan
            real_wage_growth = ((curr_year['real_wage'] / prev_year['real_wage']) - 1) * 100 if not np.isnan(prev_year['real_wage']) and prev_year['real_wage'] > 0 else np.nan
            nominal_wage_growth = ((curr_year['monthly_salary'] / prev_year['monthly_salary']) - 1) * 100 if not np.isnan(prev_year['monthly_salary']) and prev_year['monthly_salary'] > 0 else np.nan
            
            yearly_growth.append({
                'city': city,
                'year': curr_year['year'],
                'avg_employment_rate': curr_year['employment_rate'],
                'avg_monthly_salary': curr_year['monthly_salary'],
                'avg_real_wage': curr_year['real_wage'],
                'avg_population': curr_year['population'],
                'avg_housing_index': curr_year['housing_index'],
                'population_growth': population_growth,
                'real_wage_growth': real_wage_growth,
                'nominal_wage_growth': nominal_wage_growth
            })
    
    return pd.DataFrame(yearly_growth)

# Calculate Compound Annual Growth Rate (CAGR)
def calculate_cagr(data, start_year, end_year):
    """Calculate CAGR for the specified time period."""
    # Filter data for the specified time period
    yearly_data = data.groupby(['city', 'year']).agg({
        'population': 'mean',
        'real_wage': 'mean',
        'monthly_salary': 'mean'
    }).reset_index()
    
    filtered_data = yearly_data[(yearly_data['year'] >= start_year) & (yearly_data['year'] <= end_year)]
    
    cagr_results = []
    
    for city in filtered_data['city'].unique():
        city_data = filtered_data[filtered_data['city'] == city].sort_values('year')
        
        if len(city_data) >= 2:
            first_year = city_data.iloc[0]
            last_year = city_data.iloc[-1]
            
            years = end_year - start_year if end_year > start_year else 1
            
            population_cagr = (last_year['population'] / first_year['population']) ** (1/years) - 1 if not np.isnan(first_year['population']) and first_year['population'] > 0 else np.nan
            real_wage_cagr = (last_year['real_wage'] / first_year['real_wage']) ** (1/years) - 1 if not np.isnan(first_year['real_wage']) and first_year['real_wage'] > 0 else np.nan
            nominal_wage_cagr = (last_year['monthly_salary'] / first_year['monthly_salary']) ** (1/years) - 1 if not np.isnan(first_year['monthly_salary']) and first_year['monthly_salary'] > 0 else np.nan
            
            cagr_results.append({
                'city': city,
                'start_year': start_year,
                'end_year': end_year,
                'start_population': first_year['population'],
                'end_population': last_year['population'],
                'start_real_wage': first_year['real_wage'],
                'end_real_wage': last_year['real_wage'],
                'start_nominal_wage': first_year['monthly_salary'],
                'end_nominal_wage': last_year['monthly_salary'],
                'years': years,
                'population_cagr': population_cagr * 100,  # Convert to percentage
                'real_wage_cagr': real_wage_cagr * 100,
                'nominal_wage_cagr': nominal_wage_cagr * 100
            })
    
    return pd.DataFrame(cagr_results)

# Calculate growth rates and CAGR
print("Calculating growth rates...")
yearly_data_df = calculate_growth_rates(city_data_df)

# Define time period for CAGR
start_year = 2015
end_year = 2020
print(f"Calculating CAGR for {start_year}-{end_year}...")
cagr_data_df = calculate_cagr(city_data_df, start_year, end_year)

# Create visualization functions
def plot_employment_vs_population(data, selected_city=None):
    """Create a scatter plot of employment rate vs. population for all cities."""
    # Group by city and calculate the latest data point
    latest_data = data.groupby('city').apply(lambda x: x.sort_values('year').iloc[-1]).reset_index(drop=True)
    
    fig = px.scatter(
        latest_data,
        x='population',
        y='employment_rate',
        text='city',
        title="Employment Rate vs. Population by City (Latest Year)",
        labels={
            'population': 'Population',
            'employment_rate': 'Employment Rate (%)'
        },
        hover_data=['year']
    )
    
    # Highlight selected city if provided
    if selected_city:
        city_data = latest_data[latest_data['city'] == selected_city]
        if not city_data.empty:
            fig.add_trace(go.Scatter(
                x=city_data['population'],
                y=city_data['employment_rate'],
                mode='markers',
                marker=dict(color='red', size=15, line=dict(width=2, color='black')),
                name=selected_city,
                text=selected_city
            ))
    
    fig.update_traces(marker=dict(size=12), textposition='top center')
    fig.update_layout(height=600)
    return fig

def plot_population_growth_boxplot(data):
    """Create boxplots of population growth by year."""
    # Drop NaN values for population growth
    filtered_data = data.dropna(subset=['population_growth'])
    
    fig = px.box(
        filtered_data,
        x='year',
        y='population_growth',
        title="Population Growth Boxplots by Year",
        labels={
            'year': 'Year',
            'population_growth': 'Population Growth (%)'
        }
    )
    
    fig.update_layout(height=600)
    return fig

def plot_population_growth_vs_real_wages(data, selected_city=None):
    """Create a scatter plot of population growth vs. real wages."""
    # Drop NaN values
    filtered_data = data.dropna(subset=['population_growth', 'avg_real_wage'])
    
    fig = px.scatter(
        filtered_data,
        x='avg_real_wage',
        y='population_growth',
        color='city',
        hover_data=['year'],
        title="Population Growth vs. Real Wages",
        labels={
            'avg_real_wage': 'Real Wages (Monthly Salary / Housing Index)',
            'population_growth': 'Population Growth (%)'
        }
    )
    
    # Highlight selected city if provided
    if selected_city:
        city_data = filtered_data[filtered_data['city'] == selected_city]
        if not city_data.empty:
            fig.add_trace(go.Scatter(
                x=city_data['avg_real_wage'],
                y=city_data['population_growth'],
                mode='markers',
                marker=dict(color='red', size=15, line=dict(width=2, color='black')),
                name=selected_city
            ))
    
    fig.update_layout(height=600)
    return fig

def plot_cagr_real_wages_vs_population(data, selected_city=None):
    """Create a scatter plot of real wage CAGR vs. population CAGR."""
    # Drop NaN values
    filtered_data = data.dropna(subset=['real_wage_cagr', 'population_cagr'])
    
    fig = px.scatter(
        filtered_data,
        x='population_cagr',
        y='real_wage_cagr',
        text='city',
        title=f"CAGR of Real Wages vs. Population Growth ({start_year}-{end_year})",
        labels={
            'population_cagr': 'Population CAGR (%)',
            'real_wage_cagr': 'Real Wage CAGR (%)'
        }
    )
    
    # Highlight selected city if provided
    if selected_city:
        city_data = filtered_data[filtered_data['city'] == selected_city]
        if not city_data.empty:
            fig.add_trace(go.Scatter(
                x=city_data['population_cagr'],
                y=city_data['real_wage_cagr'],
                mode='markers',
                marker=dict(color='red', size=15, line=dict(width=2, color='black')),
                name=selected_city
            ))
    
    # Add a horizontal line at y=0
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    # Add a vertical line at x=0
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    
    fig.update_traces(marker=dict(size=12), textposition='top center')
    fig.update_layout(height=600)
    return fig

def plot_cagr_nominal_wages_vs_population(data, selected_city=None):
    """Create a scatter plot of nominal wage CAGR vs. population CAGR."""
    # Drop NaN values
    filtered_data = data.dropna(subset=['nominal_wage_cagr', 'population_cagr'])
    
    fig = px.scatter(
        filtered_data,
        x='population_cagr',
        y='nominal_wage_cagr',
        text='city',
        title=f"CAGR of Nominal Wages vs. Population Growth ({start_year}-{end_year})",
        labels={
            'population_cagr': 'Population CAGR (%)',
            'nominal_wage_cagr': 'Nominal Wage CAGR (%)'
        }
    )
    
    # Highlight selected city if provided
    if selected_city:
        city_data = filtered_data[filtered_data['city'] == selected_city]
        if not city_data.empty:
            fig.add_trace(go.Scatter(
                x=city_data['population_cagr'],
                y=city_data['nominal_wage_cagr'],
                mode='markers',
                marker=dict(color='red', size=15, line=dict(width=2, color='black')),
                name=selected_city
            ))
    
    # Add a horizontal line at y=0
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    # Add a vertical line at x=0
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    
    fig.update_traces(marker=dict(size=12), textposition='top center')
    fig.update_layout(height=600)
    return fig

def plot_nominal_wages_over_time(data, selected_city):
    """Create a line graph of nominal wages over time."""
    # Filter data for the selected city
    city_data = data[data['city'] == selected_city]
    
    # Group by year to get yearly averages
    yearly_data = city_data.groupby('year').agg({
        'monthly_salary': 'mean'
    }).reset_index()
    
    fig = px.line(
        yearly_data,
        x='year',
        y='monthly_salary',
        title=f"Nominal Wages Over Time for {selected_city}",
        labels={
            'year': 'Year',
            'monthly_salary': 'Monthly Nominal Salary'
        },
        markers=True
    )
    
    fig.update_layout(height=500)
    return fig

def plot_real_wages_over_time(data, selected_city):
    """Create a line graph of real wages over time."""
    # Filter data for the selected city
    city_data = data[data['city'] == selected_city]
    
    # Group by year to get yearly averages
    yearly_data = city_data.groupby('year').agg({
        'real_wage': 'mean'
    }).reset_index()
    
    fig = px.line(
        yearly_data,
        x='year',
        y='real_wage',
        title=f"Real Wages Over Time for {selected_city}",
        labels={
            'year': 'Year',
            'real_wage': 'Real Wage (Monthly Salary / Housing Index)'
        },
        markers=True
    )
    
    fig.update_layout(height=500)
    return fig

def plot_housing_costs_over_time(data, selected_city):
    """Create a line graph of housing costs over time."""
    # Filter data for the selected city
    city_data = data[data['city'] == selected_city]
    
    # Group by year to get yearly averages
    yearly_data = city_data.groupby('year').agg({
        'housing_index': 'mean'
    }).reset_index()
    
    fig = px.line(
        yearly_data,
        x='year',
        y='housing_index',
        title=f"Housing Cost Index Over Time for {selected_city}",
        labels={
            'year': 'Year',
            'housing_index': 'Housing Cost Index'
        },
        markers=True
    )
    
    fig.update_layout(height=500)
    return fig

# Create a dash app
app = dash.Dash(__name__, title="Mexico City Growth Dashboard")

# Get list of cities
cities = sorted(city_data_df['city'].unique())
default_city = cities[0] if cities else "Ciudad de México"

# Create app layout
app.layout = html.Div([
    html.H1("Mexico City Growth Diagnostics Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Select City:"),
        dcc.Dropdown(
            id='city-dropdown',
            options=[{'label': city, 'value': city} for city in cities],
            value=default_city
        )
    ], style={'width': '30%', 'margin': '20px auto'}),
    
    html.Div([
        html.H2("Overview - All Cities", style={'textAlign': 'center'}),
        
        html.Div([
            html.H3("1. Employment Rate vs. Population by City"),
            dcc.Graph(id='employment-vs-population')
        ]),
        
        html.Div([
            html.H3("2. Population Growth Boxplots by Year"),
            dcc.Graph(id='population-growth-boxplot')
        ]),
        
        html.Div([
            html.H3("3. Population Growth vs. Real Wages"),
            dcc.Graph(id='population-growth-vs-real-wages')
        ]),
        
        html.H2("CAGR Analysis", style={'textAlign': 'center'}),
        
        html.Div([
            html.H3(f"4. CAGR of Real Wages vs. Population Growth ({start_year}-{end_year})"),
            dcc.Graph(id='cagr-real-wages-vs-population')
        ]),
        
        html.Div([
            html.H3(f"5. CAGR of Nominal Wages vs. Population Growth ({start_year}-{end_year})"),
            dcc.Graph(id='cagr-nominal-wages-vs-population')
        ]),
        
        html.H2("Time Series for Selected City", style={'textAlign': 'center'}),
        
        html.Div([
            html.H3("6. Nominal Wages Over Time"),
            dcc.Graph(id='nominal-wages-over-time')
        ]),
        
        html.Div([
            html.H3("7. Real Wages Over Time"),
            dcc.Graph(id='real-wages-over-time')
        ]),
        
        html.Div([
            html.H3("8. Housing Costs Over Time"),
            dcc.Graph(id='housing-costs-over-time')
        ])
    ]),
    
    html.Div([
        html.H4("Notes:"),
        html.Ul([
            html.Li("Monthly nominal salary is calculated as hourly salary × 160 hours."),
            html.Li("Real wages are calculated as monthly salary divided by the housing cost index."),
            html.Li(f"CAGR values are calculated for the period {start_year}-{end_year}.")
        ])
    ], style={'margin': '40px 20px'})
])

# Define callbacks
@app.callback(
    [Output('employment-vs-population', 'figure'),
     Output('population-growth-boxplot', 'figure'),
     Output('population-growth-vs-real-wages', 'figure'),
     Output('cagr-real-wages-vs-population', 'figure'),
     Output('cagr-nominal-wages-vs-population', 'figure'),
     Output('nominal-wages-over-time', 'figure'),
     Output('real-wages-over-time', 'figure'),
     Output('housing-costs-over-time', 'figure')],
    [Input('city-dropdown', 'value')]
)
def update_graphs(selected_city):
    """Update all graphs based on the selected city."""
    fig1 = plot_employment_vs_population(city_data_df, selected_city)
    fig2 = plot_population_growth_boxplot(yearly_data_df)
    fig3 = plot_population_growth_vs_real_wages(yearly_data_df, selected_city)
    fig4 = plot_cagr_real_wages_vs_population(cagr_data_df, selected_city)
    fig5 = plot_cagr_nominal_wages_vs_population(cagr_data_df, selected_city)
    fig6 = plot_nominal_wages_over_time(city_data_df, selected_city)
    fig7 = plot_real_wages_over_time(city_data_df, selected_city)
    fig8 = plot_housing_costs_over_time(city_data_df, selected_city)
    
    return fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8

# Run the app
if __name__ == '__main__':
    # Save HTML output if running as script
    selected_city = default_city
    
    # Generate individual HTML files for each graph
    plot_employment_vs_population(city_data_df, selected_city).write_html("1_employment_vs_population.html")
    plot_population_growth_boxplot(yearly_data_df).write_html("2_population_growth_boxplot.html")
    plot_population_growth_vs_real_wages(yearly_data_df, selected_city).write_html("3_population_growth_vs_real_wages.html")
    plot_cagr_real_wages_vs_population(cagr_data_df, selected_city).write_html("4_cagr_real_wages_vs_population.html")
    plot_cagr_nominal_wages_vs_population(cagr_data_df, selected_city).write_html("5_cagr_nominal_wages_vs_population.html")
    plot_nominal_wages_over_time(city_data_df, selected_city).write_html("6_nominal_wages_over_time.html")
    plot_real_wages_over_time(city_data_df, selected_city).write_html("7_real_wages_over_time.html")
    plot_housing_costs_over_time(city_data_df, selected_city).write_html("8_housing_costs_over_time.html")
    
    print(f"Individual HTML files generated for {selected_city}")
    print("Starting dashboard server...")
    app.run_server(debug=True) 