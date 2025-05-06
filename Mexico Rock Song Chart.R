### RER and Employment Rates ###



pkg <- c("tidyverse", "data.table", "haven", "arrow", "htmlwidgets",
         "sjlabelled", "modelr", "ggrepel", "gghighlight", "lubridate", "tidytext",
         "plotly", "WDI", "scales", "viridis", "readr", "ggpubr", "readxl", "zoo", 
         "DBI", "duckdb", "plotly")

for (i in pkg) {
  if (!requireNamespace(i, quietly = TRUE)) {
    install.packages(i)
    library(i, character.only = TRUE)
  } else {
    library(i, character.only = TRUE)
  }
}

standard_theme <- theme(
  legend.position = "bottom",
  plot.title = element_text(hjust = .5, size = 16, color = "black", face = "bold"),
  plot.subtitle = element_text(hjust = .5),
  legend.text = element_text(size = 14, color = "black"), 
  legend.background = element_blank(),
  legend.box.background = element_blank(),
  legend.key = element_blank(),
  legend.title = element_text(size = 14, colour = "black"),
  axis.title = element_text(size = 14, colour = "black"),
  axis.text = element_text(size = 14, color = "black"), 
  strip.text = element_text(size = 14, color = "black"),
  axis.line = element_line(size = .4, colour = "black"),
  axis.ticks = element_line(size = .4, colour = "black"),
  plot.margin = margin(.3, .3, .3, .3, "cm"),
  panel.background = element_blank(),
  strip.background = element_blank(),
  panel.grid.major = element_line(size = .4, colour = "lightgrey", linetype = "longdash"))


path = "C:/Users/andfo/Dropbox (Harvard University)/Data Work Hermosillo"
setwd(path)

fua = read_dta("zonamet_expanded.dta") %>%
  mutate(ZM = ifelse(codeZM == 5, "Saltillo", ZM),
         ZM = ifelse(codeZM == 37, "San Luis Potosí", ZM))


wages_2020 = read_parquet("ceampliado_personas_2020.parquet") %>%
  select(ENT, MUN, FACTOR, INGTRMEN, COBERTURA) %>%
  collect() %>%
  mutate(geocode = paste0(ENT, MUN)) %>%
  filter(COBERTURA != 3 & INGTRMEN > 100 & INGTRMEN != 999999) %>%
  left_join(fua) %>%
  group_by(codeZM, ZM) %>%
  summarize(mean_wage = mean(INGTRMEN, na.rm = T),
            median_wage = median(INGTRMEN, na.rm = T))


rents18 = read_csv("viviendas_18.csv") %>%
  filter(cuart_dorm == 2) %>%
  mutate(geocode = substr(ubica_geo, 1, 5),
         alquiler = ifelse(!is.na(renta), renta, estim_pago)) %>%
  dplyr::select(geocode, alquiler, factor) %>%
  filter(alquiler > 0 & !is.na(alquiler)) %>%
  left_join(fua) %>%
  group_by(codeZM) %>%
  summarize(median_alquiler = median(alquiler, na.rm = T),
            mean_alquiler = weighted.mean(alquiler, w = factor, na.rm = T)) %>%
  ungroup() %>%
  mutate(nt_price = median_alquiler/mean(median_alquiler, na.rm = T))

ce2019 = read_dta("CE_2019.dta") %>%
  filter(municipio != "000" & codigo == "0") %>%
  mutate(geocode = paste0(ENTIDAD, municipio)) %>%
  left_join(fua) %>%
  group_by(codeZM, ZM) %>%
  summarize(gross_prod = sum(a111a, na.rm = T),
            gross_va = sum(a131a, na.rm = T),
            emp = sum(h001a, na.rm = T),
            payroll = sum(j000a, na.rm = T),
            prod_peremp = gross_prod*1e6/emp,
            va_peremp = gross_va*1e6/emp,
            wage_peremp = payroll*1e6/emp,
            ulc = payroll/gross_va) %>%
  filter(gross_va > 0) %>%
  ungroup() %>%
  mutate(productivity = (gross_va*1e6/emp))

ce2019 %>% head



rer_dataset = left_join(rents18, ce2019) %>%
  filter(emp >= 5e4)

ce_nat = read_dta("CE_2019.dta") %>%
  filter(municipio != "000" & codigo == "0") %>%
  summarize(gross_prod = sum(a111a, na.rm = T),
            gross_va = sum(a131a, na.rm = T),
            emp = sum(h001a, na.rm = T),
            payroll = sum(j000a, na.rm = T),
            prod_peremp = gross_prod*1e6/emp,
            va_peremp = gross_va*1e6/emp,
            wage_peremp = payroll*1e6/emp,
            ulc = payroll/gross_va) %>%
  filter(gross_va > 0)

rents18_nat = read_csv("viviendas_18.csv") %>%
  # filter(cuart_dorm == 2) %>%
  mutate(geocode = substr(ubica_geo, 1, 5),
         alquiler = ifelse(!is.na(renta), renta, estim_pago)) %>%
  dplyr::select(geocode, alquiler, factor) %>%
  filter(alquiler > 0 & !is.na(alquiler)) %>%
  summarize(median_alquiler = median(alquiler, na.rm = T),
            mean_alquiler = weighted.mean(alquiler, w = factor, na.rm = T)) %>%
  ungroup() %>%
  mutate(nt_price = mean_alquiler/mean(mean_alquiler, na.rm = T))

nat_rer = log(ce_nat$ulc) - log(rents18_nat$median_alquiler)

rer_dataset$t_index = (rer_dataset$productivity / mean(rer_dataset$productivity, na.rm = T))

rer_dataset$rer = rer_dataset$nt_price / rer_dataset$t_index

rer_dataset$unit_labor_cost = rer_dataset$payroll / rer_dataset$gross_va

rer_dataset$housing_to_wage = rer_dataset$mean_alquiler / rer_dataset$wage_peremp

rer_dataset$rer2 = rer_dataset$unit_labor_cost * rer_dataset$housing_to_wage^0.5

rer_dataset$rer3 =  (rer_dataset$productivity*rer_dataset$median_alquiler*12) / rer_dataset$wage_peremp

rer_dataset$rer_normalized = as.vector(scale(rer_dataset$rer3))

rer_dataset$rer_scaled = rer_dataset$rer3 / mean(rer_dataset$rer3, na.rm = T)

#### Net Migration ####

mig_ind = read_parquet("ceampliado_personas_2020.parquet") %>%
  select(ENT, MUN, LOC50K, TAMLOC, FACTOR, EDAD, ENT_PAIS_RES_5A, MUN_RES_5A, ENT_PAIS_TRAB, MUN_TRAB) %>%
  mutate(ENT_PAIS_RES_5A = substr(ENT_PAIS_RES_5A, 2, 3),
         ENT_PAIS_TRAB = substr(ENT_PAIS_TRAB, 2, 3)) %>%
  filter(EDAD >= 16) %>%
  collect()

mig_fua = mig_ind %>%
  mutate(geocode = paste0(ENT, MUN)) %>%
  left_join(fua)

fua2 = fua %>%
  rename(geocode_5a = geocode,
         zm_5a = ZM,
         codeZM_5a = codeZM) %>%
  select(geocode_5a, zm_5a, codeZM_5a)

mig_fua = mig_fua %>%
  mutate(geocode_5a = paste0(ENT_PAIS_RES_5A, MUN_RES_5A)) %>%
  left_join(fua2)

mig_flows_fua = mig_fua %>%
  group_by(ZM, codeZM, zm_5a, codeZM_5a) %>%
  summarize(flow = sum(FACTOR, na.rm = T)) %>%
  filter(ZM != zm_5a & !is.na(zm_5a))

fua_sonora = fua %>%
  filter(ENTIDAD == 26) %>%
  select(codeZM)

fua_sonora = fua_sonora$codeZM

aspirational_peers = c(1, 30, 34)

peers_mex = c(2, 5, 6, 10, 11, 20, 32, 37, 43, 66)

mig_flows_fua = mig_flows_fua %>%
  group_by(ZM) %>%
  mutate(total_destination = sum(flow, na.rm = T)) %>%
  group_by(zm_5a) %>%
  mutate(total_origin = sum(flow, na.rm = T)) %>%
  ungroup() %>%
  filter(total_destination > 0 | total_origin > 0)

population_fua = mig_fua %>%
  group_by(codeZM) %>%
  summarize(pop_destination = sum(FACTOR, na.rm = T)) %>%
  distinct()

mig_flows_fua = mig_flows_fua %>%
  left_join(population_fua)

population_fua = population_fua %>%
  rename(pop_origin = pop_destination)

mig_flows_fua = mig_flows_fua %>%
  left_join(population_fua, by = c("codeZM_5a" = "codeZM"))

netflows = mig_flows_fua %>%
  mutate(group = case_when(codeZM == 1763 ~ "Hermosillo",
                           codeZM %in% fua_sonora ~ "Sonora",
                           codeZM %in% aspirational_peers ~ "Aspirational mexican metropolitan areas",
                           codeZM %in% peers_mex ~ "Mexican peers",
                           TRUE ~ "Other metropolitan areas"),
         ZM = ifelse(codeZM == 37, "San Luis Potosí", ZM),
         label = ifelse(group == "Other metropolitan areas", "", ZM)) %>%
  # filter(group %in% "Mexican peers" | codeZM == 1763 | codeZM %in% aspirational_peers) %>%
  select(ZM, codeZM, total_destination, group, pop_destination) %>%
  distinct()

netflows2 = mig_flows_fua %>%
  mutate(group = case_when(codeZM == 1763 ~ "Hermosillo",
                           codeZM %in% fua_sonora ~ "Sonora",
                           codeZM %in% aspirational_peers ~ "Aspirational mexican metropolitan areas",
                           codeZM %in% peers_mex ~ "Mexican peers",
                           TRUE ~ "Other metropolitan areas"),
         ZM = ifelse(codeZM == 37, "San Luis Potosí", ZM),
         label = ifelse(group == "Other metropolitan areas", "", ZM)) %>%
  # filter(group %in% c("Hermosillo", "Mexican peers", "Aspirational mexican metropolitan areas")) %>%
  select(zm_5a, codeZM_5a, total_origin) %>%
  distinct()

netflows = netflows %>%
  left_join(netflows2, by = c("codeZM" = "codeZM_5a")) %>%
  mutate(net_flow = total_destination - total_origin,
         net_rate = net_flow*1e3/pop_destination)

rer_dataset = left_join(rer_dataset, netflows)

rer_dataset$netrate_normalized = as.vector(scale(rer_dataset$net_rate))

net_migration = rer_dataset$net_rate



rescale_to_minus1_1 = function(x) {
  # Find the data range
  min_val = min(x)
  max_val = max(x)
  
  # Calculate the maximum absolute value
  max_abs = max(abs(min_val), abs(max_val))
  
  # Scale all values proportionally to fit within [-1, 1]
  result = x / max_abs
  
  return(result)
}

rer_dataset$rescaled_migration = rescale_to_minus1_1(net_migration)

p <- rer_dataset %>% 
  mutate(wage_adj_hous = wage_peremp/mean_alquiler) %>% 
  ggplot() +
  aes(x = asinh(net_rate), y = scale(wage_adj_hous), label = ZM) +
  geom_point(aes(color = mean_alquiler), size = 5) +
  geom_text_repel(size = 7, max.overlaps = 12) +
  scale_color_continuous(high = "red", low = "green") +
  labs(color = "Mean Rent", x = "Asinh (Net Rate of Migrants) - (2015-2020)", y = "Normalized Wage to Housing Ratio (2018-19)") +
  standard_theme +
  scale_x_continuous(labels = scales::comma) +
  scale_y_continuous(labels = scales::comma) +
  geom_hline(yintercept = 0, linetype = "dashed", linewidth = 1.5, color = "grey") +
  geom_vline(xintercept = 0, linetype = "dashed", linewidth = 1.5, color = "grey") 

ggplotly(p)

saveWidget(ggplotly(p), "wage_to_rent_plot.html")


# Create the plot
p <- rer_dataset %>% 
  mutate(
    wage_adj_hous = wage_peremp / mean_alquiler,
    mean_alquiler_bracket = cut(mean_alquiler,
                                breaks = c(0, 1500, 2000, 2500, 3000, Inf),
                                labels = c("<1500", "1500-2000", "2000-2500", "2500-3000", "3000+"))) %>% 
  ggplot() +
  aes(x = asinh(net_rate), y = scale(wage_adj_hous), label = ZM) +
  geom_point(aes(color = mean_alquiler_bracket), size = 5) +
  geom_text_repel(size = 7, max.overlaps = 12) +
  scale_color_manual(
      values = c("3000+" = "#FF0000", "2500-3000" = "#FF7F00", "2000-2500" = "#FFFF00", 
                 "1500-2000" = "#7FFF00", "<1500" = "#00FF00"),
      name = "Mean Rent"
    ) +
  labs(
    x = "Asinh (Net Rate of Migrants) - (2015-2020)",
    y = "Normalized Wage to Housing Ratio (2018-19)"
  ) +
  standard_theme +
  scale_x_continuous(labels = scales::comma) +
  scale_y_continuous(labels = scales::comma) +
  geom_hline(yintercept = 0, linetype = "dashed", linewidth = 1.5, color = "grey") +
  geom_vline(xintercept = 0, linetype = "dashed", linewidth = 1.5, color = "grey") +
  theme(
    legend.position = "bottom",
    legend.direction = "horizontal",
    legend.key.width = unit(2, "cm"))

# Export to interactive HTML
ggplotly(p) %>% saveWidget("wage_to_rent_plot.html")

p_rer <- rer_dataset %>% 
  mutate(
    wage_adj_hous = wage_peremp / mean_alquiler,
    mean_alquiler_bracket = cut(mean_alquiler,
                                breaks = c(0, 1500, 2000, 2500, 3000, Inf),
                                labels = c("<1500", "1500-2000", "2000-2500", "2500-3000", "3000+"))) %>% 
  filter(rer_normalized < 4) %>% 
  ggplot() +
  aes(x = asinh(net_rate), y = rer_normalized, label = ZM) +
  geom_point(aes(color = mean_alquiler_bracket), size = 5) +
  geom_text_repel(size = 7, max.overlaps = 12) +
  scale_color_manual(
    values = c("3000+" = "#FF0000", "2500-3000" = "#FF7F00", "2000-2500" = "#FFFF00", 
               "1500-2000" = "#7FFF00", "<1500" = "#00FF00"),
    name = "Mean Rent"
  ) +
  labs(color = "", x = "Asinh (Net Rate of Migrants) - (2015-2020)", 
       y = "Normalized Productivity*Rent/Wages (2018-19)") +
  standard_theme +
  scale_x_continuous(labels = scales::comma) +
  scale_y_continuous(labels = scales::comma) +
  geom_hline(yintercept = 0, linetype = "dashed", linewidth = 3) +
  geom_vline(xintercept = 0, linetype = "dashed", linewidth = 3)

ggplotly(p_rer) %>% saveWidget("rer_and_rent_plot.html")

# ggplotly(p) %>% saveWidget("wage_to_rent_plot.html")

png("wage to housing HMO.png", res = 300, width = 27, height = 20, units = "cm")
rer_dataset %>% 
  mutate(
    wage_adj_hous = wage_peremp / mean_alquiler,
    mean_alquiler_bracket = cut(mean_alquiler,
                                breaks = c(0, 1500, 2000, 2500, 3000, Inf),
                                labels = c("<1500", "1500-2000", "2000-2500", "2500-3000", "3000+"))) %>% 
  ggplot() +
  aes(x = asinh(net_rate), y = scale(wage_adj_hous), label = ZM) +
  geom_point(aes(color = mean_alquiler_bracket), size = 5) +
  geom_text_repel(size = 4, max.overlaps = 12) +
  scale_color_manual(
    values = c("3000+" = "#FF0000", "2500-3000" = "#FF7F00", "2000-2500" = "#FFFF00", 
               "1500-2000" = "#7FFF00", "<1500" = "#00FF00"),
    name = "Mean Rent"
  ) +
  labs(
    x = "Asinh (Net Rate of Migrants) - (2015-2020)",
    y = "Normalized Wage to Housing Ratio (2018-19)"
  ) +
  standard_theme +
  scale_x_continuous(labels = scales::comma) +
  scale_y_continuous(labels = scales::comma) +
  geom_hline(yintercept = 0, linetype = "dashed", linewidth = 1.5, color = "grey") +
  geom_vline(xintercept = 0, linetype = "dashed", linewidth = 1.5, color = "grey") +
  theme(
    legend.position = "bottom",
    legend.direction = "horizontal",
    legend.key.width = unit(2, "cm"))
dev.off()

