import streamlit as st
import numpy as np
import pandas as pd
import pydeck as pdk
import plotly.express as px
from datetime import datetime

data_filepath = 'zillow_zhvi_neighborhood.csv'

st.title('Housing Prices in America')
st.markdown(
    'Explore home prices in neighborhoods across the United States '
    'based on data from Zillow'
)
st.caption(
    '*Zillow Home Value Index (ZHVI): A smoothed, seasonally-adjusted measure of the typical home value in USD*')

# @st.cache(persist=True)


def load_data():
    df = pd.read_csv(data_filepath, index_col=0)
    df.dropna(subset=['latitude', 'longitude', 'Metro'], inplace=True)
    df.drop(columns=['SizeRank', 'RegionID',
            'RegionType', 'StateName'], inplace=True)
    df.rename({'RegionName': 'Region', 'CountyName': 'County'},
              axis=1, inplace=True)
    return df


df = load_data()

df_original = df.copy()

user_state = st.selectbox("Select a state", sorted(df['State'].unique()))

user_metro = st.selectbox("Select a metro", sorted(
    df[df['State'] == user_state]['Metro'].unique()))


dates = [datetime.strptime(date, '%m-%d-%Y')
         for date in df.columns[5:-2]]

cols = []
for col in df.columns[:5]:
    cols.append(col)
for date in dates:
    cols.append(date)
for col in df.columns[-2:]:
    cols.append(col)
df.columns = cols

user_date = st.slider(
    'Select a date', value=dates[-1], min_value=dates[0], max_value=dates[-1],
    format='MMM Y')

filtered_cols = ['Region', 'State', 'City', 'County', 'latitude', 'longitude']
for date in dates:
    if date.month == user_date.month and date.year == user_date.year:
        filtered_cols.append(date)
        filtered_date = str(date)

df_filtered = df[(df['State'] == user_state) & (
    df['Metro'] == user_metro)][filtered_cols]

df_filtered.columns = filtered_cols = [
    'Region', 'State', 'City', 'County', 'latitude', 'longitude', 'ZHVI']
df_filtered.dropna(subset=['ZHVI'], inplace=True)

df_filtered['ZHVI'] = df_filtered['ZHVI'].astype(int)

# Plotting
midpoint = (np.average(df_filtered['latitude']),
            np.average(df_filtered['longitude']))


tooltip = {
    "html": "<b>Area:</b> {Region} <br> <b>ZHVI:</b> {ZHVI} <br/>",
    "style": {"color": "white"}
}

deck = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 9,
        "pitch": 70
    },
    layers=[
        pdk.Layer(
            "ColumnLayer",
            data=df_filtered,
            get_position=['longitude', 'latitude'],
            get_elevation='ZHVI',
            elevation_scale=1/100,
            get_fill_color=["ZHVI/3500", 200, 50],
            radius=75,
            opacicty=0.1,
            pickable=True,
            auto_highlight=True,
        )
    ],
    tooltip=tooltip
)

st.write(deck)
deck.to_html()

avg_zhvi = f"${round(np.average(df_filtered['ZHVI']))}"
st.metric("Average ZHVI across all neighborhoods", avg_zhvi)

if st.checkbox("Show data"):
    st.write(df_filtered[['Region', 'City', 'County', 'ZHVI']])

st.header("Typical Home Prices over Time")

user_hoods = st.multiselect('Pick neighborhood(s)',
                            df_filtered['Region'].unique())

df_hoods = pd.DataFrame(index=list(df_original.columns))
df_hoods.index.name = 'Date'


for hood in user_hoods:
    df_hood = df_original.query('Region == @hood & Metro == @user_metro')
    if len(df_hood) > 1:
        for i in df_hood.index:
            city = df_hood.loc[i]['City']
            st.markdown(f'unable to add {hood} in {city}')
    else:
        df_hoods[hood] = df_hood.transpose()

df_hoods.drop(['Region', 'State', 'City', 'Metro', 'County',
              'latitude', 'longitude'], axis=0, inplace=True)

df_hoods.index = [datetime.strptime(date, '%m-%d-%Y')
                  for date in df_hoods.index]
df_hoods = df_hoods.astype(float).round(2)
df_hoods.index = [timestamp.date() for timestamp in df_hoods.index]


if not df_hoods.empty:
    if st.checkbox("Show the data"):
        st.write(df_hoods.sort_index(
            ascending=False).style.format("${:,.0f}"))

    fig = px.line(df_hoods, x=df_hoods.index, y=df_hoods.columns)
    fig.update_xaxes(title='Time')
    fig.update_yaxes(title='Price (USD)')
    fig.update_traces(hovertemplate=None)
    st.write(fig)


st.header('Citations')
st.markdown('Zillow Research')
