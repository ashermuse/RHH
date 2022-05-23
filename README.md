# RHH
Analysis of DC Reddit Happy Hour Locations

# Running
This analysis uses the streamlit library for a front end. Execute the code using:
```
streamlit run RHH.py
```

# Setup
Setup conda envrionment:
```
conda env create -f environment.yml
```
Or install required libraries:
```
pip install -r requirements.txt
```

# Data
RHH_Events_Data.csv contains data on when and where each RHH (and UHH) has taken place

RHH_Venues.csv contains geolocation on each venue (including close metro stations). This was computed using the compute_distances and geocode jupyter scripts.

DC_Metro_Stations.csv contains geolocation on each DC Metro station and what lines service that station.