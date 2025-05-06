#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Simple script to read and display sample data from the Excel and CSV files

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import os

# Print current working directory
print("Current working directory:", os.getcwd())

# List files in the current directory
print("\nFiles in current directory:")
for file in os.listdir('.'):
    print(f" - {file}")

# Define paths to data files
try:
    employment_rate_file = "Employment rate by city.xls"
    hourly_salary_file = "Mean hourly salary by city.xls"
    population_file = "Population by city.xls"
    housing_cost_file = "Indice SHF datos abiertos 4_trim_2024(Indice SHF datos abiertos).csv"
    
    # Simple function to extract tabular data from HTML files
    def extract_data_from_html(file_path):
        print(f"\nAttempting to read: {file_path}")
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract table rows
            rows = soup.find_all('tr')
            print(f"Found {len(rows)} rows in the HTML table")
            
            # Extract first few rows to show as sample
            sample_data = []
            for i, row in enumerate(rows[:10]):  # First 10 rows
                cells = row.find_all('td')
                if cells:
                    row_data = [cell.text.strip() for cell in cells]
                    sample_data.append(row_data)
            
            return sample_data
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return []
    
    # Simple function to read CSV data
    def read_csv_sample(file_path, n_rows=5):
        print(f"\nAttempting to read: {file_path}")
        try:
            # Try to read the first few rows of the CSV
            data = pd.read_csv(file_path, sep=';', encoding='latin-1', nrows=n_rows)
            return data
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return pd.DataFrame()
    
    # Extract and display samples from each file
    employment_sample = extract_data_from_html(employment_rate_file)
    print("\nEmployment Rate Data Sample (first 5 rows, first 5 columns):")
    for i, row in enumerate(employment_sample[:5]):
        print(row[:5])
    
    salary_sample = extract_data_from_html(hourly_salary_file)
    print("\nHourly Salary Data Sample (first 5 rows, first 5 columns):")
    for i, row in enumerate(salary_sample[:5]):
        print(row[:5])
    
    population_sample = extract_data_from_html(population_file)
    print("\nPopulation Data Sample (first 5 rows, first 5 columns):")
    for i, row in enumerate(population_sample[:5]):
        print(row[:5])
    
    housing_cost_sample = read_csv_sample(housing_cost_file)
    print("\nHousing Cost Data Sample (first 5 rows):")
    print(housing_cost_sample.head())

except Exception as e:
    print(f"Error: {str(e)}")

print("\nScript execution complete.") 