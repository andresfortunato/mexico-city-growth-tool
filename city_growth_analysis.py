#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Mexico City Growth Analysis Dashboard
# This script compiles data from various Excel files and generates visualizations in Python

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import re

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

# Extract and process data
print("Reading employment data...")
employment_data, time_points = read_excel_html_table(employment_rate_file)
print("Reading salary data...")
salary_data, _ = read_excel_html_table(hourly_salary_file)
print("Reading population data...")
population_data, _ = read_excel_html_table(population_file)
print("Reading housing cost data...")
housing_cost_data = read_housing_cost(housing_cost_file)

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
                'start_population': first_year['population'],
                'end_population': last_year['population'],
                'start_real_wage': first_year['real_wage'],
                'end_real_wage': last_year['real_wage'],
                'start_nominal_wage': first_year['monthly_salary'],
                'end_nominal_wage': last_year['monthly_salary'],
                'years': years,
                'population_cagr': population_cagr,
                'real_wage_cagr': real_wage_cagr,
                'nominal_wage_cagr': nominal_wage_cagr
            })
    
    return pd.DataFrame(cagr_results)

# Calculate growth rates
print("Calculating growth rates...")
yearly_data_df = calculate_growth_rates(city_data_df)

# Calculate CAGR for a 5-year period (adjust years as needed)
start_year = 2015
end_year = 2020
print(f"Calculating CAGR for {start_year}-{end_year}...")
cagr_data_df = calculate_cagr(city_data_df, start_year, end_year)

# Display the first 5 rows of each dataset
print("\nCity Data (First 5 rows):")
print(city_data_df.head())

print("\nYearly Growth Data (First 5 rows):")
print(yearly_data_df.head())

print("\nCAGR Data (First 5 rows):")
print(cagr_data_df.head())

# Example: Create a visualization for a selected city
selected_city = "Ciudad de Monterrey"
print(f"\nSelected city for analysis: {selected_city}")

# Create visualizations (examples)

# 1. Plot employment rate vs. population
def plot_employment_vs_population(data, selected_city, start_year, end_year):
    """Create a scatter plot of employment rate vs. population."""
    filtered_data = data[
        (data['city'].isin([selected_city])) & 
        (data['year'] >= start_year) & 
        (data['year'] <= end_year)
    ].groupby(['city', 'year']).agg({
        'employment_rate': 'mean',
        'population': 'mean'
    }).reset_index()
    
    fig = px.scatter(
        filtered_data,
        x='population',
        y='employment_rate',
        text='year',
        title=f"Employment Rate vs. Population for {selected_city} ({start_year}-{end_year})",
        labels={
            'population': 'Population',
            'employment_rate': 'Employment Rate (%)'
        }
    )
    
    fig.update_traces(marker=dict(size=12, color='red'), textposition='top center')
    return fig

# Generate and save interactive plots
print("\nCreating example visualization...")
fig1 = plot_employment_vs_population(city_data_df, selected_city, start_year, end_year)
fig1.write_html("1_employment_vs_population.html")

print(f"\nAnalysis complete! Example visualization saved as HTML file.")
print(f"Selected city: {selected_city}")
print(f"Period: {start_year} to {end_year}") 