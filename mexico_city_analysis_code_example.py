#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mexico City Growth Analysis - Code Example

This script demonstrates how to process the data files and create
the visualizations needed for the Mexico City growth diagnostics.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from bs4 import BeautifulSoup
import re

# Set plotting styles
plt.style.use('seaborn')
sns.set_palette("Set2")

# 1. Functions to read and clean data
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

# 2. Function to compile all data into a single DataFrame
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

# 3. Function to calculate growth rates
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

# 4. Function to calculate CAGR
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
                'years': years,
                'population_cagr': population_cagr * 100,  # Convert to percentage
                'real_wage_cagr': real_wage_cagr * 100,
                'nominal_wage_cagr': nominal_wage_cagr * 100
            })
    
    return pd.DataFrame(cagr_results)

# 5. Visualization functions

def plot_employment_vs_population(data, selected_city, start_year, end_year):
    """Create scatter plot of employment rate vs. population (Fig. 1)."""
    # Filter data for the selected years
    filtered_data = data[
        (data['year'] >= start_year) & 
        (data['year'] <= end_year)
    ].groupby(['city', 'year']).agg({
        'employment_rate': 'mean',
        'population': 'mean'
    }).reset_index()
    
    # Get latest available year for each city
    latest_data = filtered_data.loc[filtered_data.groupby('city')['year'].idxmax()]
    
    # Create figure
    fig = px.scatter(
        latest_data,
        x='population',
        y='employment_rate',
        text='city',
        title=f"Employment Rate vs. Population ({start_year}-{end_year})",
        labels={
            'population': 'Population',
            'employment_rate': 'Employment Rate (%)'
        },
        color_discrete_sequence=['blue']
    )
    
    # Highlight selected city
    selected_data = latest_data[latest_data['city'] == selected_city]
    if not selected_data.empty:
        fig.add_trace(
            go.Scatter(
                x=selected_data['population'],
                y=selected_data['employment_rate'],
                text=selected_data['city'],
                mode='markers+text',
                marker=dict(color='red', size=12),
                textposition='top center',
                name=selected_city
            )
        )
    
    # Format
    fig.update_layout(
        xaxis_title="Population",
        yaxis_title="Employment Rate (%)",
        legend_title="City"
    )
    
    return fig

def plot_population_growth_boxplot(yearly_data, selected_city):
    """Create boxplot of population growth (Fig. 2)."""
    # Get years in the data
    years = sorted(yearly_data['year'].unique())
    
    # Create figure
    fig = go.Figure()
    
    # Add boxplots for each year
    for year in years:
        year_data = yearly_data[yearly_data['year'] == year]
        fig.add_trace(
            go.Box(
                y=year_data['population_growth'],
                name=str(year),
                boxpoints=False
            )
        )
        
        # Add marker for selected city
        selected_city_data = year_data[year_data['city'] == selected_city]
        if not selected_city_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=[str(year)],
                    y=selected_city_data['population_growth'],
                    mode='markers',
                    marker=dict(color='red', size=10),
                    showlegend=False
                )
            )
    
    # Update layout
    fig.update_layout(
        title=f"Population Growth Rate Distributions by Year with {selected_city} highlighted",
        xaxis_title="Year",
        yaxis_title="Population Growth Rate (%)"
    )
    
    return fig

def plot_population_growth_vs_real_wages(yearly_data, selected_city):
    """Create scatter of population growth vs. real wages (Fig. 3)."""
    # Create figure
    fig = px.scatter(
        yearly_data,
        x='population_growth',
        y='avg_real_wage',
        text='city',
        color='year',
        title=f"Population Growth vs. Real Wages with {selected_city} highlighted",
        labels={
            'population_growth': 'Population Growth (%)',
            'avg_real_wage': 'Real Wage (Monthly Salary / Housing Index)'
        }
    )
    
    # Highlight selected city
    selected_data = yearly_data[yearly_data['city'] == selected_city]
    fig.add_trace(
        go.Scatter(
            x=selected_data['population_growth'],
            y=selected_data['avg_real_wage'],
            text=selected_data['city'],
            mode='markers',
            marker=dict(color='red', size=12),
            name=selected_city
        )
    )
    
    return fig

def plot_cagr_scatter(cagr_data, selected_city, x_var, y_var, x_label, y_label, title):
    """Create scatter plot of CAGR variables (Figs. 4-5)."""
    fig = px.scatter(
        cagr_data,
        x=x_var,
        y=y_var,
        text='city',
        title=title,
        labels={
            x_var: x_label,
            y_var: y_label
        }
    )
    
    # Highlight selected city
    selected_data = cagr_data[cagr_data['city'] == selected_city]
    if not selected_data.empty:
        fig.add_trace(
            go.Scatter(
                x=selected_data[x_var],
                y=selected_data[y_var],
                text=selected_data['city'],
                mode='markers+text',
                marker=dict(color='red', size=12),
                textposition='top center',
                name=selected_city
            )
        )
    
    return fig

def plot_time_series(city_data, selected_city, value_col, value_label, title):
    """Create time series line plots (Figs. 6-8)."""
    # Calculate median values across all cities for each time point
    city_data_by_year = city_data.groupby(['year', 'quarter']).agg({
        value_col: 'median'
    }).reset_index()
    city_data_by_year['time_point'] = city_data_by_year['year'].astype(str) + 'Q' + city_data_by_year['quarter'].astype(str)
    
    # Filter data for selected city
    selected_city_data = city_data[city_data['city'] == selected_city]
    
    # Create figure
    fig = go.Figure()
    
    # Add line for median of all cities
    fig.add_trace(
        go.Scatter(
            x=city_data_by_year['time_point'],
            y=city_data_by_year[value_col],
            mode='lines',
            name='Median of All Cities',
            line=dict(color='gray')
        )
    )
    
    # Add line for selected city
    fig.add_trace(
        go.Scatter(
            x=selected_city_data['time_point'],
            y=selected_city_data[value_col],
            mode='lines+markers',
            name=selected_city,
            line=dict(color='red')
        )
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Time Period",
        yaxis_title=value_label,
        xaxis=dict(
            tickmode='array',
            tickvals=city_data_by_year['time_point'][::4],  # Show every 4th tick (annual)
            tickangle=45
        )
    )
    
    return fig

# Example of how to use the functions:
def main():
    # For a real implementation, replace this with actual data file paths
    employment_rate_file = "Employment rate by city.xls"
    hourly_salary_file = "Mean hourly salary by city.xls"
    population_file = "Population by city.xls"
    housing_cost_file = "Indice SHF datos abiertos 4_trim_2024(Indice SHF datos abiertos).csv"
    
    try:
        # 1. Read data files
        print("Reading data files...")
        employment_data, time_points = read_excel_html_table(employment_rate_file)
        salary_data, _ = read_excel_html_table(hourly_salary_file)
        population_data, _ = read_excel_html_table(population_file)
        housing_cost_data = read_housing_cost(housing_cost_file)
        
        # 2. Compile data
        print("Compiling data...")
        city_data = compile_data(employment_data, salary_data, population_data, housing_cost_data, time_points)
        
        # 3. Calculate growth rates and CAGR
        print("Calculating growth rates...")
        yearly_data = calculate_growth_rates(city_data)
        
        # 4. Calculate CAGR for a specific period
        start_year = 2015
        end_year = 2020
        print(f"Calculating CAGR for {start_year}-{end_year}...")
        cagr_data = calculate_cagr(city_data, start_year, end_year)
        
        # 5. Create visualizations for a selected city
        selected_city = "Ciudad de Monterrey"
        print(f"Creating visualizations for {selected_city}...")
        
        # Fig 1: Employment vs. Population
        fig1 = plot_employment_vs_population(city_data, selected_city, start_year, end_year)
        fig1.write_html("1_employment_vs_population.html")
        
        # Fig 2: Population Growth Boxplots
        fig2 = plot_population_growth_boxplot(yearly_data, selected_city)
        fig2.write_html("2_population_growth_boxplot.html")
        
        # Fig 3: Population Growth vs. Real Wages
        fig3 = plot_population_growth_vs_real_wages(yearly_data, selected_city)
        fig3.write_html("3_population_growth_vs_real_wages.html")
        
        # Fig 4: CAGR Real Wages vs. Population Growth
        fig4 = plot_cagr_scatter(
            cagr_data, 
            selected_city,
            'real_wage_cagr', 
            'population_cagr',
            'Real Wage CAGR (%)',
            'Population CAGR (%)',
            f"CAGR of Real Wages vs. Population Growth ({start_year}-{end_year})"
        )
        fig4.write_html("4_cagr_real_wages_vs_population.html")
        
        # Fig 5: CAGR Nominal Wages vs. Population Growth
        fig5 = plot_cagr_scatter(
            cagr_data, 
            selected_city,
            'nominal_wage_cagr', 
            'population_cagr',
            'Nominal Wage CAGR (%)',
            'Population CAGR (%)',
            f"CAGR of Nominal Wages vs. Population Growth ({start_year}-{end_year})"
        )
        fig5.write_html("5_cagr_nominal_wages_vs_population.html")
        
        # Fig 6: Nominal Wages Time Series
        fig6 = plot_time_series(
            city_data,
            selected_city,
            'monthly_salary',
            'Monthly Nominal Salary (MXN)',
            f"Nominal Wages Over Time for {selected_city} vs. Median of All Cities"
        )
        fig6.write_html("6_nominal_wages_time_series.html")
        
        # Fig 7: Real Wages Time Series
        fig7 = plot_time_series(
            city_data,
            selected_city,
            'real_wage',
            'Real Wage (Monthly Salary / Housing Index)',
            f"Real Wages Over Time for {selected_city} vs. Median of All Cities"
        )
        fig7.write_html("7_real_wages_time_series.html")
        
        # Fig 8: Housing Cost Index Time Series
        fig8 = plot_time_series(
            city_data,
            selected_city,
            'housing_index',
            'Housing Cost Index',
            f"Housing Cost Index Over Time for {selected_city} vs. Median of All Cities"
        )
        fig8.write_html("8_housing_cost_time_series.html")
        
        print("Visualizations have been saved as HTML files.")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 