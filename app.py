import streamlit as st
import pandas as pd
import pvlib
from main import *
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title='Balcony Solar Power Tool ', page_icon='🌞', initial_sidebar_state="expanded")

@st.cache_data()
def get_solar_radiation_data(latitude, longitude, panel_angle, panel_azimuth, pv_tech, horizon_data, system_losses):
    data, _, _ = pvlib.iotools.get_pvgis_hourly(
        latitude=latitude,
        longitude=longitude,
        start=pd.Timestamp('2016-01-01'),
        end=pd.Timestamp('2020-12-31'),
        raddatabase='PVGIS-SARAH2',
        surface_tilt=panel_angle,
        surface_azimuth=panel_azimuth,
        pvcalculation=True,
        peakpower=0.001,
        usehorizon=True,
        pvtechchoice=pv_tech,
        userhorizon=horizon_data,
        components=False,
        mountingplace='building',
        loss=system_losses*100,
        url='https://re.jrc.ec.europa.eu/api/v5_2/',
    )
    solar_data = data[['P']].copy()
    return solar_data




def plot_average_generation(solar_data):
    solar_data['Month'] = solar_data.index.month
    seasons = {
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Fall', 10: 'Fall', 11: 'Fall'
    }
    season_colors = {
        'Winter': 'blue',
        'Spring': 'green',
        'Summer': 'red',
        'Fall': 'orange'
    }

    solar_data['Season'] = solar_data['Month'].map(seasons)
    avg_radiation = solar_data.groupby(['Season', solar_data.index.hour])['P'].mean()

    fig = go.Figure()

    for season, color in season_colors.items():
        seasonal_data = avg_radiation[season]
        fig.add_trace(go.Scatter(x=seasonal_data.index, y=seasonal_data.values, mode='lines', name=season, line=dict(color=color)))

    fig.update_layout(
        title='Average Hourly Energy Generation per kW of installed solar panels',
        xaxis_title='Hour of the Day',
        yaxis_title='Energy generated [kWh/kW]'
    )
    return fig

def plot_energy_vs_size(panel_sizes, energy_generated, payback_time):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=panel_sizes, y=energy_generated, mode='lines+markers', name='Energy Generated', yaxis='y1', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=panel_sizes, y=payback_time, mode='lines+markers', name='Payback Time', yaxis='y2', line=dict(color='red')))

    fig.update_layout(
        title='Energy Generation and payoff time vs. panel size',
        xaxis_title='Panel Size [W]',
        yaxis_title='Energy Generation [kWh/Year]',
        yaxis2=dict(title='Payback Time [Years]', overlaying='y', side='right')
    )
    return fig


def plot_energy_vs_size(panel_sizes, energy_generated, payback_time):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=panel_sizes, y=energy_generated, mode='lines+markers', name='Energy Generated', yaxis='y1', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=panel_sizes, y=payback_time, mode='lines+markers', name='Payback Time', yaxis='y2', line=dict(color='red')))

    fig.update_layout(
        title='Energy Generation and payoff time vs. panel size',
        xaxis_title='Panel Size [W]',
        yaxis_title='Energy Generation [kWh/Year]',
        yaxis2=dict(title='Payback Time [Years]', overlaying='y', side='right')
    )
    return fig

def plot_balance_over_time(panel_sizes, balances, solar_data):
    fig = go.Figure()

    for i, balance in enumerate(balances):
        years_since_start = (solar_data.index - solar_data.index[0]).days / 365
        label = f'Panel Size: {panel_sizes[i]} W'
        fig.add_trace(go.Scatter(x=years_since_start, y=balance, mode='lines', name=label, line=dict(color=px.colors.sequential.Viridis[i])))

    fig.add_shape(
        type='line',
        y0=0, y1=0,
        x0=min(years_since_start), x1=max(years_since_start),
        line=dict(color='White')
    )

    fig.update_layout(
        title='Return over time vs. panel size',
        xaxis_title='Time [Years]',
        yaxis_title='Balance [euros]'
    )
    return fig



def plot_results(panel_sizes, energy_generated, payback_time, balances, solar_data, max_inverter_power, panel_angle, panel_azimuth, show=False):
    # Plot average solar radiation
    avg_gen_fig = plot_average_generation(solar_data)
    # Plot energy generation versus panel size and payback time
    energy_vs_size_fig = plot_energy_vs_size(panel_sizes, energy_generated, payback_time)
    # Plot balance over time for different panel sizes with labels
    balance_over_time_fig = plot_balance_over_time(panel_sizes, balances, solar_data)

    st.plotly_chart(avg_gen_fig,use_container_width=True)
    st.plotly_chart(energy_vs_size_fig,use_container_width=True)
    st.plotly_chart(balance_over_time_fig,use_container_width=True)



def app():
    st.title("Solar Panel Study")
    st.markdown("""This app wil help you analyze the ideal size of solar panels, tailored for the Berlin subsidy program for mini balcony solar powerplants.
                Given user-defined parameters, it calculates various metrics, including energy generation and payback time, based on  parameters and solar radiation data. 
                It provides insights to optimize your solar power setup.
                """)
    st.markdown("""
                - Credits to __riparise__ fot the original repo with calculation logic: [solar-panel-sizing-tool](https://github.com/riparise/solar-panel-sizing-tool/)
                - Author: [gniewus](https://www.linkedin.com/in/tomtkaczyk/)
                """)
    st.markdown("")
    # Input widgets for each parameter    
    with st.sidebar:

        st.header("Parameters")
        c1, c2 = st.columns(2)
        longitude = c1.number_input('Longitude', value=13.40)
        latitude = c2.number_input('Latitude', value=52.52)
        panel_price = c1.number_input('Panel Price (EUR per W)', min_value=0.0, value=0.52)
        installation_costs = c2.number_input('Installation Costs (EUR)', min_value=0, value=30)
        energy_cost_per_kwh = st.number_input('Energy Cost per kWh (EUR)', min_value=0.0, value=0.35)
        subsidy_amount = st.number_input('Subsidy Amount (EUR)', min_value=0, value=500)
        max_inverter_power = st.number_input('Max Inverter Power (W)', min_value=0, value=600)
        panel_azimuth = st.slider('Panel Azimuth', min_value=0, max_value=360, value=245)
        panel_angle = st.slider('Panel Angle', min_value=0, max_value=90, value=90)
        inverter_efficiency = st.slider('Inverter Efficiency', min_value=0.0, max_value=1.0, value=0.91)
        
    
        pv_tech = st.selectbox('PV Tech', options=['crystSi', 'CIS', 'CdTe', 'Unknown'], index=0)
        system_losses = st.slider('System Losses', min_value=0.0, max_value=1.0, value=0.05)
        unused_energy = st.slider('Unused Energy', min_value=0.0, max_value=1.0, value=0.4)
        horizon_data = st.multiselect('Horizon Data', options=[90, 20], default=[90, 90, 90, 20, 20, 20, 90, 90])
    
        panel_sizes = st.multiselect('Panel Sizes (W)', options=[600, 800, 1000, 1100, 1200, 1300, 1400], default=[600, 800, 1000, 1100, 1200, 1300, 1400])
    
    #st.subheader('Solar Panel Study')

    btn = st.button('Submit','submit')
    # Convert string inputs to proper format
 
    
    if btn:
        # Retrieve solar radiation data
        solar_data = get_solar_radiation_data(latitude, longitude, panel_angle, panel_azimuth, pv_tech, horizon_data, system_losses)
        
        # Calculate trade-off metrics
        energy_generated, payback_time, balances = calculate_trade_off(solar_data,
                                                                       max_inverter_power,
                                                                       panel_price,
                                                                       installation_costs,
                                                                       inverter_efficiency,
                                                                       energy_cost_per_kwh,
                                                                       subsidy_amount,
                                                                       panel_sizes, unused_energy)
        
        # Plot and display results
        plot_results(panel_sizes, energy_generated, payback_time, balances, solar_data, max_inverter_power, panel_angle, panel_azimuth)
        st.map((pd.DataFrame([(latitude, longitude)],columns= ['lat','lon'])), zoom=13,use_container_width=True)

if __name__ == '__main__':
    app()
