import datetime
import streamlit as st
import pandas as pd
#import geopandas as gpd
import plotly.graph_objs as go
import plotly.express as px

class RHH:
    def __init__(self):
        self.mapbox_access_token = open('../credentials/mapbox_key.txt').read()
        self.google_API_key = open('../credentials/google_api_key.txt').read()
        px.set_mapbox_access_token(self.mapbox_access_token)

    def compute_metro_preference(self):
        for index, row in self.happy_hours.iterrows():
            close_metros = row['Closest Metros'].replace('[', '').replace(']', '').replace('"', '').replace("'", '').split(',')
            close_metros = [metro.strip() for metro in close_metros]
            close_lines = []
            
            for metro in close_metros:
                lines = self.metro_stations.loc[self.metro_stations['Name'] == metro]['Line']
                for line in lines:
                    lines_list = line.split(',')
                    close_lines.extend(lines_list)
            
            close_lines = list(set(close_lines))
            close_lines = [line.strip() for line in close_lines]
            
            for line in close_lines:
                self.metro_lines[line] += 1

    def backend(self):
        self.happy_hours = pd.read_csv("../data/RHH_Events_Data.csv")
        self.happy_hours['Date'] = pd.to_datetime(self.happy_hours['Date']).dt.date

        self.venues = pd.read_csv("../data/RHH_Venues.csv")

        self.happy_hours = self.happy_hours.join(self.venues.set_index('Venue'), on='Venue', how='outer').drop('Visits', axis=1)
        self.happy_hours = self.happy_hours.sort_values(by=['Date'], ascending=False)


        self.metro_stations = pd.read_csv("../data/DC_Metro_Stations.csv")
        self.metro_lines = {'blue':0,'orange':0,'silver':0,'red':0,'green':0,'yellow':0}
        

        #Grouped by DC/VA neighborhoods as defined by OpenGov (DC) and OSM (VA/MD)
        #Temperature


    def frontend(self):
        st.title("DC Reddit Happy Hour")
    
        # Update the happy_hours based on selected date range
        start_date = st.sidebar.date_input('Front date', value = min(self.happy_hours['Date']), min_value = min(self.happy_hours['Date']), max_value = datetime.date.today())
        end_date = st.sidebar.date_input('End date', value = datetime.date.today(), min_value = min(self.happy_hours['Date']), max_value = datetime.date.today())
        self.happy_hours = self.happy_hours.loc[(self.happy_hours['Date'] > start_date) & (self.happy_hours['Date'] < end_date)]

        filter = st.sidebar.radio('Official HH Toggle', ['Both', 'Official', 'Unofficial'])
        if filter == 'Official':
            self.happy_hours = self.happy_hours.loc[self.happy_hours['Official']]
        elif filter == 'Unofficial':
            self.happy_hours = self.happy_hours.loc[self.happy_hours['Official'] == False]

        st.title("Happy Hour Map")
        fig = go.Figure()

        # Happy Hours
        fig.add_trace(go.Scattermapbox(
                lat=self.happy_hours['lat'],
                lon=self.happy_hours['lon'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=10,
                    color='teal',
                    opacity=1
                ),
                text= "<b>" + self.happy_hours['Venue'] + "</b><br>" + self.happy_hours['Closest Metros'],
                hovertemplate="%{text}<extra></extra>"
            ))

        # Metro Stations
        fig.add_trace(go.Scattermapbox(
                lat=self.metro_stations['lat'],
                lon=self.metro_stations['lon'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=7,
                    color='black',
                    opacity=0.8
                ),
                text=self.metro_stations['Line'],
                hoverinfo='text'
            ))

        fig.update_layout(
            title='Happy Hour Locations & Metro Locations',
            autosize=True,
            hovermode='closest',
            showlegend=False,
            mapbox=dict(
                accesstoken=self.mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=38.9072,
                    lon=-77.0369
                ),
                pitch=0,
                zoom=10,
                style='streets'
            ),
        )

        st.plotly_chart(fig)

        st.title("Metro Preferences")

        self.compute_metro_preference()
        df_metro_lines = pd.DataFrame.from_dict(self.metro_lines, orient='index', columns=['Visits'])
        df_metro_lines['Metro Line'] = df_metro_lines.index
        fig = px.bar(df_metro_lines, x='Metro Line', y='Visits', color='Metro Line', color_discrete_sequence=['blue', 'orange', 'silver', 'red', 'green', 'yellow'])
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig)

        st.write(self.happy_hours)

    def start(self):
        self.backend()
        self.frontend()

    
if __name__ == "__main__":
    EDA_tool = RHH()
    EDA_tool.start()

