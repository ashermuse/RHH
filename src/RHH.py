import datetime
import streamlit as st
import pandas as pd
#import geopandas as gpd
import plotly.graph_objs as go
import plotly.express as px
import random
from googleapiclient.discovery import build

class RHH:
    def __init__(self):
        try:
            self.mapbox_access_token = open('../credentials/mapbox_key.txt').read()
            self.google_api_key = open('../credentials/google_api_key.txt').read()
        except:
            self.mapbox_access_token = st.secrets["mapbox_token"]
            self.google_api_key = st.secrets["google_api_key"]
        px.set_mapbox_access_token(self.mapbox_access_token)

    def compute_metro_preference(self):
        for index, row in self.happy_hours.iterrows():
            close_metros = row['Closest Metros']
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
        
    def metro_cleanup(self, metros):
        metros = metros.split(',')
        for i in range(len(metros)):
            metros[i] = metros[i].strip('\'"[] ')
        return metros
    
    def get_metro_lines(self, metros):
        lines = []
        for metro in metros:
            lines.extend(self.metro_stations.loc[self.metro_stations['Name'] == metro].iloc[0, 4].replace(' ', '').split(','))
        lines = list(set(lines))
        return lines

    def data_from_sheets(self, name, id):
        service = build('sheets', 'v4', developerKey=self.google_api_key)

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=id,
                                    range= name + '!A:AA').execute()
        values = result.get('values', [])

        df = pd.DataFrame(values)
        df.columns = df.iloc[0]
        df = df.drop(0)
        df = df.reset_index().drop(columns=['index'])
        return df

    def backend(self):
        try:
            self.happy_hours = pd.read_csv("../data/RHH_Events_Data.csv")
            self.venues = pd.read_csv("../data/RHH_Venues.csv")
            self.metro_stations = pd.read_csv("../data/DC_Metro_Stations.csv")
        except:
            self.happy_hours    = self.data_from_sheets("RHH_Events_Data", "1JDFP204BOKw1z057S9dvT3d0ND9u7FYu0IhjotkxUhE")
            self.venues         = self.data_from_sheets("RHH_Venues", "1gd2dX3rmsD9R6IE7ncDwbeaVRj0sFonunaJqx939MZw")
            self.metro_stations = self.data_from_sheets("DC_Metro_Stations", "1ACHprBIkogbxG-Uz_L3mpIqZpAiNou47ZtTC6BaCYBs")

        self.happy_hours['Date'] = pd.to_datetime(self.happy_hours['Date']).dt.date

        self.happy_hours = self.happy_hours.join(self.venues.set_index('Venue'), on='Venue', how='outer').drop('Visits', axis=1)
        self.happy_hours = self.happy_hours.sort_values(by=['Date'], ascending=False)

        self.happy_hours = self.happy_hours.astype({"did_rain":bool})
        self.happy_hours["Temperature"] = pd.to_numeric(self.happy_hours["Temperature"])
        self.happy_hours["Wind_Speed"] = pd.to_numeric(self.happy_hours["Wind_Speed"])
        self.happy_hours["Relative_Humidity"] = pd.to_numeric(self.happy_hours["Relative_Humidity"])

        self.happy_hours['Closest Metros'] = self.happy_hours['Closest Metros'].apply(self.metro_cleanup)
        self.happy_hours['Closest Metros Label'] = self.happy_hours['Closest Metros'].apply(lambda metros: ', '.join(metros))
        
        self.metro_lines = {'blue':0,'orange':0,'silver':0,'red':0,'green':0,'yellow':0}
        
    def frontend(self):
        st.title("DC Reddit Happy Hour Analytics")
    
        # Update the happy_hours based on selected date range
        start_date = st.sidebar.date_input('Start Cutoff', value = min(self.happy_hours['Date']), min_value = min(self.happy_hours['Date']), max_value = datetime.date.today())
        end_date = st.sidebar.date_input('End Cutoff', value = datetime.date.today(), min_value = min(self.happy_hours['Date']), max_value = datetime.date.today())
        self.happy_hours = self.happy_hours.loc[(self.happy_hours['Date'] > start_date) & (self.happy_hours['Date'] < end_date)]

        filter = st.sidebar.radio('Official HH Toggle', ['Both', 'Official', 'Unofficial'])
        if filter == 'Official':
            self.happy_hours = self.happy_hours.loc[self.happy_hours['Official']]
        elif filter == 'Unofficial':
            self.happy_hours = self.happy_hours.loc[self.happy_hours['Official'] == False]

       

        AI_HH_loc = st.sidebar.button('Generate Happy Hour Location')
        ai_options = st.sidebar.checkbox('AI Options')
        if ai_options:
            ai_metro_lines = st.sidebar.multiselect("Must Use: Metro Lines", ['blue','orange','silver','red','green','yellow'])
        
        if AI_HH_loc:
            ai_df = self.happy_hours
            if ai_options:
                if len(ai_metro_lines) != 0:
                    ai_df['Metro Lines'] = ai_df['Closest Metros'].apply(lambda metros: self.get_metro_lines(metros))
                    ai_df = ai_df.loc[ai_df['Metro Lines'].apply(lambda metro_lines: any(x in metro_lines for x in ai_metro_lines))]

            AI_HH_venue = ai_df['Venue'].sample().iloc[0]
            st.sidebar.title("HAPPY HOUR LOCATION:")
            st.sidebar.subheader(AI_HH_venue)

        st.subheader("Happy Hour Map")
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
                text= "<b>" + self.happy_hours['Venue'] + "</b><br>" + self.happy_hours['Closest Metros Label'],
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

        st.subheader("Weather Statistics")
        col1, col2 = st.columns(2)
        col1.metric("Temperature", str(self.happy_hours['Temperature'].mean())[0:4] + " °F")
        col2.metric("Wind", str(self.happy_hours['Wind_Speed'].mean())[0:4] + " km/h")
        col1, col2 = st.columns(2)
        col1.metric("Humidity", str(self.happy_hours['Relative_Humidity'].mean())[0:4] + "%")
        col2.metric("Rain", str(self.happy_hours['did_rain'].value_counts(normalize=True).loc[True]*100)[0:4] + "%")

        st.subheader("Metro Preferences")

        self.compute_metro_preference()
        df_metro_lines = pd.DataFrame.from_dict(self.metro_lines, orient='index', columns=['Visits'])
        df_metro_lines['Metro Line'] = df_metro_lines.index
        fig = px.bar(df_metro_lines, x='Metro Line', y='Visits', color='Metro Line', color_discrete_sequence=['blue', 'orange', 'silver', 'red', 'green', 'yellow'])
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig)

        st.subheader("Venue Preferences")
        venue_counts = self.happy_hours.groupby(by='Venue').count()
        fig = px.bar(venue_counts, x=venue_counts.index, y='Number')
        st.plotly_chart(fig)

        st.subheader("Raw Data")
        st.write(self.happy_hours)

    def start(self):
        self.backend()
        self.frontend()

    
if __name__ == "__main__":
    EDA_tool = RHH()
    EDA_tool.start()

