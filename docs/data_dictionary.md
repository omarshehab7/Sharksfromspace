# Data Dictionary

Ocean data variables used in the Sharks From Space prediction model.

## Primary Variables

| Variable | Unit | Source | Description |
|---|---|---|---|
| `sst` | °C | GHRSST MUR, MODIS | Sea surface temperature measured by satellite infrared sensors |
| `sst_anomaly` | °C | Computed | Deviation of SST from the long-term climatological mean |
| `sst_gradient` | °C/km | Computed | Spatial rate of change of SST; indicates thermal fronts |
| `chlorophyll` | mg/m³ | MODIS Aqua | Chlorophyll-a concentration; proxy for phytoplankton abundance |
| `depth` | meters | ETOPO 2022 | Bathymetric depth (negative = below sea level) |
| `current_speed` | m/s | OSCAR | Ocean surface current speed |
| `current_direction` | degrees | OSCAR | Ocean surface current direction (0° = north) |
| `salinity` | PSU | SMAP/Aquarius | Practical salinity units |

## Derived Features (ML Model Input)

| Feature | Description | Why It Matters |
|---|---|---|
| `sst` | Absolute SST | Different shark species prefer specific temperature ranges |
| `sst_anomaly` | SST anomaly | Warm anomalies can indicate prey aggregation events |
| `sst_gradient` | Thermal front strength | Fronts concentrate plankton and fish, attracting sharks |
| `chlorophyll` | Phytoplankton density | Base of the food chain — more plankton = more prey |
| `depth` | Water depth | Continental shelf depths (20-200m) are preferred by many species |
| `distance_to_coast_km` | Shore proximity | Many species are coastal predators |
| `day_of_year` | Julian day | Captures seasonal migration patterns |
| `month` | Calendar month | Seasonal signal for species activity |

## Risk Score Interpretation

| Score Range | Risk Level | Color | Meaning |
|---|---|---|---|
| 0.0 – 0.3 | Low | 🟢 Green | Normal ocean conditions, low shark activity likelihood |
| 0.3 – 0.6 | Medium | 🟠 Orange | Moderate conditions for shark activity |
| 0.6 – 1.0 | High | 🔴 Red | Strong indicators of shark activity; exercise caution |

## Data Sources

| Source | Agency | URL |
|---|---|---|
| GHRSST MUR SST | NASA PO.DAAC | https://podaac.jpl.nasa.gov/GHRSST |
| MODIS Ocean Color | NASA OB.DAAC | https://oceancolor.gsfc.nasa.gov/ |
| ETOPO 2022 | NOAA NCEI | https://www.ncei.noaa.gov/products/etopo-global-relief-model |
| OSCAR Currents | NASA PO.DAAC | https://podaac.jpl.nasa.gov/dataset/OSCAR_L4_OC_NRT_V2.0 |
