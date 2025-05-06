# Mexico City Growth Analysis Dashboard
# This script compiles data from various Excel files and generates visualizations

# Load required libraries
library(readxl)
library(dplyr)
library(ggplot2)
library(plotly)
library(tidyr)

# Define paths to data files
employment_rate_file <- "Employment rate by city.xls"
hourly_salary_file <- "Mean hourly salary by city.xls"
population_file <- "Population by city.xls"
housing_cost_file <- "Indice SHF datos abiertos 4_trim_2024(Indice SHF datos abiertos).csv"

# Read and clean data
read_excel_html_table <- function(file_path) {
  # Read file content
  content <- readLines(file_path, warn = FALSE)
  content <- paste(content, collapse = "\n")
  
  # Extract table rows
  rows <- unlist(strsplit(content, "<tr[^>]*>"))
  
  # Initialize variables
  column_names <- c()
  data <- list()
  city_data <- list()
  
  # Process data
  for (i in 7:length(rows)) { # Skip header rows
    cells <- unlist(regmatches(rows[i], gregexpr("<td[^>]*>(.*?)</td>", rows[i])))
    if (length(cells) > 0) {
      values <- sapply(cells, function(cell) {
        content <- gsub("<td[^>]*>", "", cell)
        content <- gsub("</td>", "", content)
        content <- gsub("<[^>]*>", "", content) # Remove any other HTML tags
        return(content)
      })
      
      if (length(values) > 1) {
        city_name <- values[1]
        city_data[[city_name]] <- as.numeric(values[-1])
      }
    }
  }
  
  return(city_data)
}

# Read housing cost data
read_housing_cost <- function(file_path) {
  # Read CSV file with semicolon separator
  data <- read.csv(file_path, sep = ";", stringsAsFactors = FALSE, fileEncoding = "latin1")
  
  # Filter for ZM (zona metropolitana) entries
  zm_data <- data[grep("^ZM", data$Global), ]
  
  # Create a lookup from city name to index values
  result <- list()
  zm_names <- unique(zm_data$Global)
  
  for (zm in zm_names) {
    city_name <- sub("^ZM ", "", zm)
    if (city_name == "Valle México") city_name <- "Ciudad de México"
    if (city_name == "PueblaTlax") city_name <- "Ciudad de Puebla"
    
    # Get all rows for this ZM
    zm_rows <- zm_data[zm_data$Global == zm, ]
    
    # Create time series
    years <- zm_rows$Año
    quarters <- zm_rows$Trimestre
    time_points <- paste0(years, "Q", quarters)
    values <- zm_rows$Indice
    
    result[[city_name]] <- data.frame(
      time_point = time_points,
      year = years,
      quarter = quarters,
      index = values,
      stringsAsFactors = FALSE
    )
  }
  
  return(result)
}

# Extract and process data
employment_data <- read_excel_html_table(employment_rate_file)
salary_data <- read_excel_html_table(hourly_salary_file)
population_data <- read_excel_html_table(population_file)
housing_cost_data <- read_housing_cost(housing_cost_file)

# Compile data into a single dataset
compile_data <- function(employment_data, salary_data, population_data, housing_cost_data) {
  # Get all city names
  all_cities <- unique(c(names(employment_data), names(salary_data), names(population_data)))
  
  # Get all years and quarters
  years <- 2005:2024
  quarters <- 1:4
  time_points <- expand.grid(year = years, quarter = quarters)
  time_points$time_point <- paste0(time_points$year, "Q", time_points$quarter)
  
  # Initialize result dataframe
  result <- data.frame()
  
  for (city in all_cities) {
    if (city == "Áreas metropolitanas" || city == "") next
    
    # Get data for this city
    emp_values <- if (city %in% names(employment_data)) employment_data[[city]] else rep(NA, length(time_points$time_point))
    salary_values <- if (city %in% names(salary_data)) salary_data[[city]] else rep(NA, length(time_points$time_point))
    pop_values <- if (city %in% names(population_data)) population_data[[city]] else rep(NA, length(time_points$time_point))
    
    # Find matching housing cost data
    city_housing <- NULL
    # Try different name formats
    city_simple_name <- gsub("Ciudad de ", "", city)
    if (city_simple_name %in% names(housing_cost_data)) {
      city_housing <- housing_cost_data[[city_simple_name]]
    } else if (city %in% names(housing_cost_data)) {
      city_housing <- housing_cost_data[[city]]
    }
    
    # Create city dataframe
    city_df <- data.frame(
      city = city,
      time_point = time_points$time_point,
      year = time_points$year,
      quarter = time_points$quarter,
      employment_rate = emp_values,
      hourly_salary = salary_values,
      population = pop_values,
      stringsAsFactors = FALSE
    )
    
    # Add housing cost if available
    if (!is.null(city_housing)) {
      city_df <- merge(city_df, city_housing, by = c("time_point", "year", "quarter"), all.x = TRUE)
    } else {
      city_df$index <- NA
    }
    
    # Calculate monthly salary (hourly salary * 160 hours)
    city_df$monthly_salary <- city_df$hourly_salary * 160
    
    # Calculate real wages (monthly salary / housing cost index)
    city_df$real_wage <- city_df$monthly_salary / city_df$index
    
    # Append to result
    result <- rbind(result, city_df)
  }
  
  return(result)
}

# Compile the data
city_data <- compile_data(employment_data, salary_data, population_data, housing_cost_data)

# Calculate year-over-year population growth rates
calculate_growth_rates <- function(data) {
  # Group by city and year, taking the average for each year
  yearly_data <- data %>%
    group_by(city, year) %>%
    summarize(
      avg_employment_rate = mean(employment_rate, na.rm = TRUE),
      avg_monthly_salary = mean(monthly_salary, na.rm = TRUE),
      avg_real_wage = mean(real_wage, na.rm = TRUE),
      avg_population = mean(population, na.rm = TRUE),
      avg_housing_index = mean(index, na.rm = TRUE),
      .groups = "drop"
    )
  
  # Calculate year-over-year growth rates
  result <- yearly_data %>%
    group_by(city) %>%
    arrange(city, year) %>%
    mutate(
      population_growth = (avg_population / lag(avg_population) - 1) * 100,
      real_wage_growth = (avg_real_wage / lag(avg_real_wage) - 1) * 100,
      nominal_wage_growth = (avg_monthly_salary / lag(avg_monthly_salary) - 1) * 100
    ) %>%
    ungroup()
  
  return(result)
}

# Calculate Compound Annual Growth Rate (CAGR)
calculate_cagr <- function(data, start_year, end_year) {
  # Filter data for the specified time period
  filtered_data <- data %>%
    filter(year >= start_year & year <= end_year) %>%
    group_by(city) %>%
    summarize(
      start_population = first(avg_population[year == min(year)]),
      end_population = last(avg_population[year == max(year)]),
      start_real_wage = first(avg_real_wage[year == min(year)]),
      end_real_wage = last(avg_real_wage[year == max(year)]),
      start_nominal_wage = first(avg_monthly_salary[year == min(year)]),
      end_nominal_wage = last(avg_monthly_salary[year == max(year)]),
      .groups = "drop"
    ) %>%
    mutate(
      years = end_year - start_year,
      population_cagr = (end_population / start_population)^(1/years) - 1,
      real_wage_cagr = (end_real_wage / start_real_wage)^(1/years) - 1,
      nominal_wage_cagr = (end_nominal_wage / start_nominal_wage)^(1/years) - 1
    )
  
  return(filtered_data)
}

# Calculate growth rates
yearly_data <- calculate_growth_rates(city_data)

# Calculate CAGR for a 5-year period (adjust years as needed)
cagr_data <- calculate_cagr(yearly_data, 2015, 2020)

# Create visualization functions
# 1. Employment rate vs. population by city (levels)
plot_employment_vs_population <- function(data, selected_city, start_year, end_year) {
  filtered_data <- data %>%
    filter(year >= start_year & year <= end_year) %>%
    group_by(city, year) %>%
    summarize(
      avg_employment_rate = mean(employment_rate, na.rm = TRUE),
      avg_population = mean(population, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    filter(!is.na(avg_employment_rate) & !is.na(avg_population))
  
  # Create the plot
  p <- ggplot(filtered_data, aes(x = avg_population, y = avg_employment_rate, color = city == selected_city)) +
    geom_point(alpha = 0.6, size = 3) +
    geom_text(data = filtered_data %>% filter(city == selected_city),
              aes(label = year), vjust = -1, hjust = 0.5, size = 3) +
    scale_color_manual(values = c("FALSE" = "grey", "TRUE" = "red")) +
    labs(
      title = paste("Employment Rate vs. Population (", start_year, "-", end_year, ")", sep = ""),
      subtitle = paste("Selected city:", selected_city),
      x = "Population",
      y = "Employment Rate (%)"
    ) +
    theme_minimal() +
    theme(legend.position = "none")
  
  return(ggplotly(p))
}

# 2. Population growth compared to other cities BOXPLOTs by year
plot_population_growth_boxplot <- function(data, selected_city) {
  # Create the plot
  p <- ggplot(data, aes(x = factor(year), y = population_growth)) +
    geom_boxplot() +
    geom_point(data = data %>% filter(city == selected_city),
               aes(x = factor(year), y = population_growth), color = "red", size = 3) +
    labs(
      title = "Population Growth by Year",
      subtitle = paste("Selected city:", selected_city, "(red dots)"),
      x = "Year",
      y = "Population Growth (%)"
    ) +
    theme_minimal() +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))
  
  return(ggplotly(p))
}

# 3. SCATTER of population growth VS real wages
plot_growth_vs_real_wages <- function(data, selected_city, start_year, end_year) {
  filtered_data <- data %>%
    filter(year >= start_year & year <= end_year) %>%
    group_by(city) %>%
    summarize(
      avg_population_growth = mean(population_growth, na.rm = TRUE),
      avg_real_wage = mean(avg_real_wage, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    filter(!is.na(avg_population_growth) & !is.na(avg_real_wage))
  
  # Create the plot
  p <- ggplot(filtered_data, aes(x = avg_real_wage, y = avg_population_growth, color = city == selected_city)) +
    geom_point(alpha = 0.7, size = 3) +
    geom_text(data = filtered_data %>% filter(city == selected_city | avg_population_growth > quantile(filtered_data$avg_population_growth, 0.9)),
              aes(label = city), vjust = -1, hjust = 0.5, size = 3) +
    scale_color_manual(values = c("FALSE" = "grey", "TRUE" = "red")) +
    labs(
      title = paste("Population Growth vs. Real Wages (", start_year, "-", end_year, ")", sep = ""),
      subtitle = paste("Selected city:", selected_city),
      x = "Average Real Wage (Wages/Housing Cost)",
      y = "Average Population Growth (%)"
    ) +
    theme_minimal() +
    theme(legend.position = "none")
  
  return(ggplotly(p))
}

# 4. CAGR Real wages VS population growth
plot_cagr_real_wages_vs_population <- function(cagr_data, selected_city) {
  # Create the plot
  p <- ggplot(cagr_data, aes(x = real_wage_cagr * 100, y = population_cagr * 100, color = city == selected_city)) +
    geom_point(alpha = 0.7, size = 3) +
    geom_text(data = cagr_data %>% filter(city == selected_city | abs(real_wage_cagr) > quantile(abs(cagr_data$real_wage_cagr), 0.9, na.rm = TRUE)),
              aes(label = city), vjust = -1, hjust = 0.5, size = 3) +
    scale_color_manual(values = c("FALSE" = "grey", "TRUE" = "red")) +
    labs(
      title = paste("CAGR of Real Wages vs. Population Growth (", min(cagr_data$years) + min(yearly_data$year), "-", max(yearly_data$year), ")", sep = ""),
      subtitle = paste("Selected city:", selected_city),
      x = "CAGR of Real Wages (%)",
      y = "CAGR of Population (%)"
    ) +
    theme_minimal() +
    theme(legend.position = "none")
  
  return(ggplotly(p))
}

# 5. CAGR Nominal wages VS population growth
plot_cagr_nominal_wages_vs_population <- function(cagr_data, selected_city) {
  # Create the plot
  p <- ggplot(cagr_data, aes(x = nominal_wage_cagr * 100, y = population_cagr * 100, color = city == selected_city)) +
    geom_point(alpha = 0.7, size = 3) +
    geom_text(data = cagr_data %>% filter(city == selected_city | abs(nominal_wage_cagr) > quantile(abs(cagr_data$nominal_wage_cagr), 0.9, na.rm = TRUE)),
              aes(label = city), vjust = -1, hjust = 0.5, size = 3) +
    scale_color_manual(values = c("FALSE" = "grey", "TRUE" = "red")) +
    labs(
      title = paste("CAGR of Nominal Wages vs. Population Growth (", min(cagr_data$years) + min(yearly_data$year), "-", max(yearly_data$year), ")", sep = ""),
      subtitle = paste("Selected city:", selected_city),
      x = "CAGR of Nominal Wages (%)",
      y = "CAGR of Population (%)"
    ) +
    theme_minimal() +
    theme(legend.position = "none")
  
  return(ggplotly(p))
}

# 6. Line graph of nominal wages by year for specific city and another line for median of cities
plot_nominal_wages_time_series <- function(data, selected_city) {
  # Calculate median wages across all cities by year
  median_wages <- data %>%
    group_by(year) %>%
    summarize(
      median_monthly_salary = median(avg_monthly_salary, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    mutate(city = "Median of all cities")
  
  # Get data for the selected city
  selected_city_data <- data %>%
    filter(city == selected_city) %>%
    select(year, avg_monthly_salary) %>%
    rename(median_monthly_salary = avg_monthly_salary) %>%
    mutate(city = selected_city)
  
  # Combine data
  combined_data <- rbind(median_wages, selected_city_data)
  
  # Create the plot
  p <- ggplot(combined_data, aes(x = year, y = median_monthly_salary, color = city)) +
    geom_line(size = 1) +
    geom_point(size = 2) +
    labs(
      title = "Nominal Wages by Year",
      subtitle = paste("Selected city:", selected_city, "vs. Median of all cities"),
      x = "Year",
      y = "Monthly Salary (hourly * 160)"
    ) +
    theme_minimal() +
    scale_color_manual(values = c("Median of all cities" = "blue", selected_city = "red"))
  
  return(ggplotly(p))
}

# 7. Line graph of real wages by year for specific city and another line for median of cities
plot_real_wages_time_series <- function(data, selected_city) {
  # Calculate median real wages across all cities by year
  median_wages <- data %>%
    group_by(year) %>%
    summarize(
      median_real_wage = median(avg_real_wage, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    mutate(city = "Median of all cities")
  
  # Get data for the selected city
  selected_city_data <- data %>%
    filter(city == selected_city) %>%
    select(year, avg_real_wage) %>%
    rename(median_real_wage = avg_real_wage) %>%
    mutate(city = selected_city)
  
  # Combine data
  combined_data <- rbind(median_wages, selected_city_data)
  
  # Create the plot
  p <- ggplot(combined_data, aes(x = year, y = median_real_wage, color = city)) +
    geom_line(size = 1) +
    geom_point(size = 2) +
    labs(
      title = "Real Wages by Year",
      subtitle = paste("Selected city:", selected_city, "vs. Median of all cities"),
      x = "Year",
      y = "Real Wage (Monthly Salary / Housing Cost Index)"
    ) +
    theme_minimal() +
    scale_color_manual(values = c("Median of all cities" = "blue", selected_city = "red"))
  
  return(ggplotly(p))
}

# 8. Line graph of housing costs
plot_housing_costs_time_series <- function(data, selected_city) {
  # Calculate median housing costs across all cities by year
  median_housing <- data %>%
    group_by(year) %>%
    summarize(
      median_housing_index = median(avg_housing_index, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    mutate(city = "Median of all cities")
  
  # Get data for the selected city
  selected_city_data <- data %>%
    filter(city == selected_city) %>%
    select(year, avg_housing_index) %>%
    rename(median_housing_index = avg_housing_index) %>%
    mutate(city = selected_city)
  
  # Combine data
  combined_data <- rbind(median_housing, selected_city_data)
  
  # Create the plot
  p <- ggplot(combined_data, aes(x = year, y = median_housing_index, color = city)) +
    geom_line(size = 1) +
    geom_point(size = 2) +
    labs(
      title = "Housing Cost Index by Year",
      subtitle = paste("Selected city:", selected_city, "vs. Median of all cities"),
      x = "Year",
      y = "Housing Cost Index"
    ) +
    theme_minimal() +
    scale_color_manual(values = c("Median of all cities" = "blue", selected_city = "red"))
  
  return(ggplotly(p))
}

# Example usage: select a city and create all plots
selected_city <- "Ciudad de Monterrey"  # Change to any city in the dataset
start_year <- 2015
end_year <- 2020

# Create and save plots
plot1 <- plot_employment_vs_population(city_data, selected_city, start_year, end_year)
plot2 <- plot_population_growth_boxplot(yearly_data, selected_city)
plot3 <- plot_growth_vs_real_wages(yearly_data, selected_city, start_year, end_year)
plot4 <- plot_cagr_real_wages_vs_population(cagr_data, selected_city)
plot5 <- plot_cagr_nominal_wages_vs_population(cagr_data, selected_city)
plot6 <- plot_nominal_wages_time_series(yearly_data, selected_city)
plot7 <- plot_real_wages_time_series(yearly_data, selected_city)
plot8 <- plot_housing_costs_time_series(yearly_data, selected_city)

# Save plots to HTML files
library(htmlwidgets)
saveWidget(plot1, "1_employment_vs_population.html")
saveWidget(plot2, "2_population_growth_boxplot.html")
saveWidget(plot3, "3_growth_vs_real_wages.html")
saveWidget(plot4, "4_cagr_real_wages_vs_population.html")
saveWidget(plot5, "5_cagr_nominal_wages_vs_population.html")
saveWidget(plot6, "6_nominal_wages_time_series.html")
saveWidget(plot7, "7_real_wages_time_series.html")
saveWidget(plot8, "8_housing_costs_time_series.html")

# Print a message
cat("Analysis complete! All plots have been saved as HTML files.\n")
cat("Selected city:", selected_city, "\n")
cat("Period:", start_year, "to", end_year, "\n") 