#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mexico City Growth Data Sample Generator
This script simulates the data compilation process using generated sample data.
"""

import pandas as pd
import numpy as np

def generate_sample_data():
    """Generate sample data for Mexico cities.
    
    Returns:
        pd.DataFrame: Dataframe with sample city data
    """
    print("Generating sample city data...")
    
    # Define cities
    cities = [
        "Ciudad de México", 
        "Ciudad de Guadalajara", 
        "Ciudad de Monterrey", 
        "Ciudad de Puebla", 
        "Ciudad de León"
    ]
    
    # Define years and quarters
    years = list(range(2015, 2021))  # 2015-2020
    quarters = list(range(1, 5))
    
    # Base values for different cities
    population_base = {
        "Ciudad de México": 19_000_000,
        "Ciudad de Guadalajara": 4_000_000,
        "Ciudad de Monterrey": 4_200_000,
        "Ciudad de Puebla": 2_100_000,
        "Ciudad de León": 1_500_000
    }
    
    employment_base = {
        "Ciudad de México": 58,
        "Ciudad de Guadalajara": 61,
        "Ciudad de Monterrey": 63,
        "Ciudad de Puebla": 56,
        "Ciudad de León": 59
    }
    
    hourly_salary_base = {
        "Ciudad de México": 45,
        "Ciudad de Guadalajara": 38,
        "Ciudad de Monterrey": 42,
        "Ciudad de Puebla": 33,
        "Ciudad de León": 35
    }
    
    housing_index_base = {
        "Ciudad de México": 150,
        "Ciudad de Guadalajara": 100,
        "Ciudad de Monterrey": 120,
        "Ciudad de Puebla": 85,
        "Ciudad de León": 80
    }
    
    # Create sample data
    data = []
    
    for city in cities:
        # City-specific growth rates (annual)
        pop_growth = np.random.uniform(0.005, 0.025)  # 0.5% to 2.5% annual growth
        emp_growth = np.random.uniform(-0.01, 0.02)  # -1% to +2% annual change
        salary_growth = np.random.uniform(0.02, 0.07)  # 2% to 7% annual growth
        housing_growth = np.random.uniform(0.03, 0.08)  # 3% to 8% annual growth
        
        # Generate data for each year and quarter
        for year in years:
            for quarter in quarters:
                # Calculate time index (0 to 5.75)
                year_idx = year - 2015
                time_idx = year_idx + (quarter - 1) / 4
                
                # Calculate values with growth trends and random variation
                population = population_base[city] * (1 + pop_growth) ** time_idx * (1 + np.random.uniform(-0.005, 0.005))
                emp_rate = employment_base[city] * (1 + emp_growth) ** time_idx * (1 + np.random.uniform(-0.01, 0.01))
                hourly_salary = hourly_salary_base[city] * (1 + salary_growth) ** time_idx * (1 + np.random.uniform(-0.02, 0.02))
                housing_index = housing_index_base[city] * (1 + housing_growth) ** time_idx * (1 + np.random.uniform(-0.02, 0.02))
                
                # Calculate derived metrics
                monthly_salary = hourly_salary * 160
                real_wage = monthly_salary / housing_index
                
                # Add row
                data.append({
                    'city': city,
                    'year': year,
                    'quarter': quarter,
                    'time_point': f"{year}Q{quarter}",
                    'population': population,
                    'employment_rate': emp_rate,
                    'hourly_salary': hourly_salary,
                    'housing_index': housing_index,
                    'monthly_salary': monthly_salary,
                    'real_wage': real_wage
                })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    print(f"Generated {len(df)} data points for {len(cities)} cities")
    return df

def calculate_growth_rates(data):
    """Calculate year-over-year growth rates.
    
    Args:
        data (pd.DataFrame): Combined dataset with all metrics
        
    Returns:
        pd.DataFrame: Dataset with yearly growth rates
    """
    print("Calculating year-over-year growth rates...")
    
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
            
            # Calculate growth rates
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
    
    df = pd.DataFrame(yearly_growth)
    print(f"Created growth rates dataframe with {len(df)} rows")
    return df

def calculate_cagr(data, start_year, end_year):
    """Calculate CAGR for the specified time period.
    
    Args:
        data (pd.DataFrame): Combined dataset with all metrics
        start_year (int): Start year for CAGR calculation
        end_year (int): End year for CAGR calculation
        
    Returns:
        pd.DataFrame: Dataset with CAGR metrics
    """
    print(f"Calculating CAGR for period {start_year}-{end_year}...")
    
    # Group data by city and year
    yearly_data = data.groupby(['city', 'year']).agg({
        'population': 'mean',
        'real_wage': 'mean',
        'monthly_salary': 'mean'
    }).reset_index()
    
    # Filter for relevant years
    filtered_data = yearly_data[(yearly_data['year'] >= start_year) & (yearly_data['year'] <= end_year)]
    
    cagr_results = []
    
    for city in filtered_data['city'].unique():
        city_data = filtered_data[filtered_data['city'] == city].sort_values('year')
        
        if len(city_data) >= 2:
            first_year = city_data.iloc[0]
            last_year = city_data.iloc[-1]
            
            years = end_year - start_year
            
            # Calculate CAGR
            population_cagr = (last_year['population'] / first_year['population']) ** (1/years) - 1
            real_wage_cagr = (last_year['real_wage'] / first_year['real_wage']) ** (1/years) - 1
            nominal_wage_cagr = (last_year['monthly_salary'] / first_year['monthly_salary']) ** (1/years) - 1
            
            cagr_results.append({
                'city': city,
                'start_year': start_year,
                'end_year': end_year,
                'years': years,
                'population_cagr': population_cagr * 100,  # Convert to percentage
                'real_wage_cagr': real_wage_cagr * 100,
                'nominal_wage_cagr': nominal_wage_cagr * 100
            })
    
    df = pd.DataFrame(cagr_results)
    print(f"Created CAGR dataframe with {len(df)} rows")
    return df

def format_df_printout(df):
    """Format a dataframe for better console output.
    
    Args:
        df (pd.DataFrame): Dataframe to format
        
    Returns:
        str: Formatted string representation
    """
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.precision', 2)
    return df.to_string()

def main():
    """Main function to run the data generation and processing."""
    try:
        # Generate sample data
        city_data = generate_sample_data()
        
        # Calculate growth rates
        yearly_growth = calculate_growth_rates(city_data)
        
        # Calculate CAGR for 2015-2020
        start_year = 2015
        end_year = 2020
        cagr_data = calculate_cagr(city_data, start_year, end_year)
        
        # Display the first 5 rows of each dataset
        print("\n===== CITY DATA (First 5 rows) =====")
        print(format_df_printout(city_data.head()))
        
        print("\n===== YEARLY GROWTH DATA (First 5 rows) =====")
        print(format_df_printout(yearly_growth.head()))
        
        print("\n===== CAGR DATA (First 5 rows) =====")
        print(format_df_printout(cagr_data.head()))
        
        # Print data summary
        print("\n===== DATA SUMMARY =====")
        print(f"Total cities: {city_data['city'].nunique()}")
        print(f"Time period: {city_data['year'].min()}-{city_data['year'].max()}")
        print(f"Total data points: {len(city_data)}")
        
        # Show how monthly nominal salary is calculated
        print("\n===== CALCULATION EXAMPLE =====")
        sample_row = city_data.iloc[0]
        print(f"For {sample_row['city']} in {sample_row['time_point']}:")
        print(f"  Hourly salary: ${sample_row['hourly_salary']:.2f} MXN")
        print(f"  Monthly salary = Hourly salary * 160 hours = ${sample_row['monthly_salary']:.2f} MXN")
        print(f"  Housing index: {sample_row['housing_index']:.2f}")
        print(f"  Real wage = Monthly salary / Housing index = {sample_row['real_wage']:.2f}")
        
        return {
            "city_data": city_data,
            "yearly_growth": yearly_growth,
            "cagr_data": cagr_data
        }
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        return None

if __name__ == "__main__":
    main() 