#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Simple script to show sample data for Mexico city growth analysis

import pandas as pd
import numpy as np

# Create sample data to demonstrate the analysis
def create_sample_data():
    # Cities
    cities = [
        "Ciudad de México", 
        "Ciudad de Guadalajara", 
        "Ciudad de Monterrey", 
        "Ciudad de Puebla", 
        "Ciudad de León"
    ]
    
    # Years
    years = list(range(2015, 2021))  # 2015-2020
    
    # Create sample data
    data = []
    
    # Population (millions)
    population_base = {
        "Ciudad de México": 19.0,
        "Ciudad de Guadalajara": 4.0,
        "Ciudad de Monterrey": 4.2,
        "Ciudad de Puebla": 2.1,
        "Ciudad de León": 1.5
    }
    
    # Employment rate (%)
    employment_base = {
        "Ciudad de México": 58,
        "Ciudad de Guadalajara": 61,
        "Ciudad de Monterrey": 63,
        "Ciudad de Puebla": 56,
        "Ciudad de León": 59
    }
    
    # Hourly salary (MXN)
    hourly_salary_base = {
        "Ciudad de México": 45,
        "Ciudad de Guadalajara": 38,
        "Ciudad de Monterrey": 42,
        "Ciudad de Puebla": 33,
        "Ciudad de León": 35
    }
    
    # Housing cost index
    housing_cost_base = {
        "Ciudad de México": 150,
        "Ciudad de Guadalajara": 100,
        "Ciudad de Monterrey": 120,
        "Ciudad de Puebla": 85,
        "Ciudad de León": 80
    }
    
    # Generate data with realistic growth patterns
    for city in cities:
        # City-specific growth rates
        pop_growth = np.random.uniform(0.005, 0.025)  # 0.5% to 2.5% annual growth
        emp_growth = np.random.uniform(-0.01, 0.02)  # -1% to +2% annual change
        salary_growth = np.random.uniform(0.02, 0.07)  # 2% to 7% annual growth
        housing_growth = np.random.uniform(0.03, 0.08)  # 3% to 8% annual growth
        
        for year in years:
            for quarter in range(1, 5):  # 4 quarters per year
                year_index = year - 2015
                time_index = year_index + (quarter - 1) / 4
                
                # Calculate values with some random variation
                pop = population_base[city] * (1 + pop_growth) ** time_index * (1 + np.random.uniform(-0.005, 0.005))
                emp = employment_base[city] * (1 + emp_growth) ** time_index * (1 + np.random.uniform(-0.01, 0.01))
                salary = hourly_salary_base[city] * (1 + salary_growth) ** time_index * (1 + np.random.uniform(-0.02, 0.02))
                housing = housing_cost_base[city] * (1 + housing_growth) ** time_index * (1 + np.random.uniform(-0.02, 0.02))
                
                # Calculate monthly salary and real wage
                monthly_salary = salary * 160  # 160 hours per month
                real_wage = monthly_salary / housing
                
                # Add row to data
                data.append({
                    "city": city,
                    "year": year,
                    "quarter": quarter,
                    "time_point": f"{year}Q{quarter}",
                    "population": pop * 1_000_000,  # Convert to actual population
                    "employment_rate": emp,
                    "hourly_salary": salary,
                    "housing_index": housing,
                    "monthly_salary": monthly_salary,
                    "real_wage": real_wage
                })
    
    # Convert to DataFrame
    return pd.DataFrame(data)

# Create sample data
city_data = create_sample_data()

# Calculate yearly averages and growth rates
def calculate_growth_rates(data):
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
            
            population_growth = ((curr_year['population'] / prev_year['population']) - 1) * 100
            real_wage_growth = ((curr_year['real_wage'] / prev_year['real_wage']) - 1) * 100
            nominal_wage_growth = ((curr_year['monthly_salary'] / prev_year['monthly_salary']) - 1) * 100
            
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
            
            years = end_year - start_year
            
            population_cagr = (last_year['population'] / first_year['population']) ** (1/years) - 1
            real_wage_cagr = (last_year['real_wage'] / first_year['real_wage']) ** (1/years) - 1
            nominal_wage_cagr = (last_year['monthly_salary'] / first_year['monthly_salary']) ** (1/years) - 1
            
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
yearly_data = calculate_growth_rates(city_data)

# Calculate CAGR for a 5-year period
start_year = 2015
end_year = 2020
cagr_data = calculate_cagr(city_data, start_year, end_year)

# Display the first 5 rows of each dataset
print("\nCity Data (First 5 rows):")
print(city_data.head())

print("\nYearly Growth Data (First 5 rows):")
print(yearly_data.head())

print("\nCAGR Data (First 5 rows):")
print(cagr_data.head())

# Show key insights for a selected city
selected_city = "Ciudad de Monterrey"
print(f"\nSelected city for analysis: {selected_city}")

# 1. Population growth
print("\nPopulation Growth:")
city_yearly = yearly_data[yearly_data['city'] == selected_city].sort_values('year')
for _, row in city_yearly.iterrows():
    print(f"  {row['year']}: {row['population_growth']:.2f}% (Population: {row['avg_population']/1_000_000:.2f} million)")

# 2. Employment rate
print("\nEmployment Rate:")
for _, row in city_yearly.iterrows():
    print(f"  {row['year']}: {row['avg_employment_rate']:.2f}%")

# 3. Wages
print("\nNominal Monthly Wages:")
for _, row in city_yearly.iterrows():
    print(f"  {row['year']}: ${row['avg_monthly_salary']:.2f} MXN")

# 4. Real Wages
print("\nReal Wages (Monthly Salary / Housing Index):")
for _, row in city_yearly.iterrows():
    print(f"  {row['year']}: {row['avg_real_wage']:.2f}")

# 5. Housing Cost Index
print("\nHousing Cost Index:")
for _, row in city_yearly.iterrows():
    print(f"  {row['year']}: {row['avg_housing_index']:.2f}")

# 6. CAGR Summary
city_cagr = cagr_data[cagr_data['city'] == selected_city]
print(f"\nCompound Annual Growth Rate ({start_year}-{end_year}):")
print(f"  Population CAGR: {city_cagr['population_cagr'].values[0]*100:.2f}%")
print(f"  Nominal Wage CAGR: {city_cagr['nominal_wage_cagr'].values[0]*100:.2f}%")
print(f"  Real Wage CAGR: {city_cagr['real_wage_cagr'].values[0]*100:.2f}%")

print("\nAnalysis Notes:")
print("  For monthly nominal salary, we calculate hourly salary * 160 hours.")
print("  For real wages, we divide the monthly salary by the housing cost index.")
print("  The CAGR figures show the average annual growth rates over the specified period.")
print("  Employment rate represents the percentage of working-age population that is employed.") 