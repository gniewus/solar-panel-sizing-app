import streamlit as st
import pandas as pd
import pvlib
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import plotly.io as pio
import tempfile, plotly
from datetime import datetime,timedelta


st.set_page_config(layout='wide', page_title='Balcony Solar Power Tool ', page_icon='🌞', initial_sidebar_state="expanded"
                                  ,menu_items={ 'About': "mailto: tom.tkaczyk11@gmail.com"})
                   

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



def report_download_btn(figs: list[plotly.graph_objects.Figure],params_df: pd.DataFrame):
    # Convert figures to HTML
    html_figs = [pio.to_html(fig, full_html=False,include_plotlyjs=True) for fig in figs]
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w+t')
    
    with open(temp_file.name, "rb") as file:
        temp_file.write('<html><head><title> Berlin Balcony solar panel ROI </title></head><body>')
        temp_file.write('<h3> Parameters </h3>')
        temp_file.write(params_df.to_html())
        temp_file.write('<h3> Results </h3>')
        for f in html_figs:
            temp_file.write(f)
        temp_file.write('</body></html>')
        
        st.download_button(
            label="Download this report as HTML",
            data=file,
            file_name="report.html",
            mime="application/html",
            use_container_width=True
        ) 

    return temp_file.name


@st.cache_data(ttl='30s')
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

@st.cache_data(ttl='30s')
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

st.cache_data(ttl='30s')
def plot_balance_over_time(panel_sizes, balances, solar_data):
    fig = go.Figure()

    for i, balance in enumerate(balances):

        time_frame = [datetime.today()+ x for x in (solar_data.index - solar_data.index[0])]
        label = f'Panel Size: {panel_sizes[i]} W'
        fig.add_trace(go.Scatter(x=time_frame, y=balance, mode='lines', name=label, line=dict(color=px.colors.sequential.Viridis[i]),hovertemplate = '%{y:.2f}EUR'))

    fig.add_shape(
        type='line',
        y0=0, y1=0,
        x0=min(time_frame), x1=max(time_frame),
        line=dict(color='darkgrey', width=2, dash='dash'),
        
    )

    fig.update_layout(
        title='Return over time vs. panel size',
        xaxis_title='Time [Years]',
        yaxis_title='Balance [euros]'
    )
    return fig


def plot_results(panel_sizes, energy_generated, payback_time, balances, solar_data, max_inverter_power, panel_angle, panel_azimuth, show=False):

    msg = "Calculating... "
    prgrs=st.progress(1,msg) 
    prgrs.progress(10, msg)
    energy_vs_size_fig = plot_energy_vs_size(panel_sizes, energy_generated, payback_time)
    prgrs.progress(30,msg)
    avg_gen_fig = plot_average_generation(solar_data)
    prgrs.progress(60,msg)
    balance_over_time_fig = plot_balance_over_time(panel_sizes, balances, solar_data)
    prgrs.progress(90,msg)
    st.plotly_chart(balance_over_time_fig,use_container_width=True)
    prgrs.progress(93,'Plotting...')
    st.plotly_chart(energy_vs_size_fig,use_container_width=True)
    prgrs.progress(96)
    st.plotly_chart(avg_gen_fig,use_container_width=True)
    prgrs.progress(100)
    prgrs.empty()

    return avg_gen_fig, energy_vs_size_fig, balance_over_time_fig


@st.cache_data(persist=True)
def calculate_trade_off(solar_data, max_inverter_power, panel_price, installation_costs,
                        inverter_efficiency, energy_cost_per_kwh, subsidy_amount, panel_sizes, unused_energy):
    energy_generated, payback_time, balances = [], [], []
    if type(panel_price) is list and len(panel_price) != len(panel_sizes):
        raise ValueError('Panel price is not a single coefficient, but also not the same size as the panel sizes')

    num_years = (solar_data.index[-1] - solar_data.index[0]).days / 365

    for i, panel_size in enumerate(panel_sizes):
        # Calculate energy generation and financial metrics
        energy_per_hour = np.minimum(panel_size * solar_data['P'], max_inverter_power)
        if type(panel_price) is list:
            initial_cost = panel_price[i] + installation_costs
        else:
            initial_cost = panel_size * panel_price + installation_costs
        income = energy_per_hour * inverter_efficiency * energy_cost_per_kwh * (1-unused_energy) / 1000
        balances.append(min(-initial_cost + subsidy_amount, 0) + np.cumsum(income))

        total_energy_generated = sum(energy_per_hour) * inverter_efficiency * (1-unused_energy)
        energy_generated.append(total_energy_generated / (num_years * 1000))

        payback_time.append(max(initial_cost - subsidy_amount, 0) / (energy_generated[-1] * energy_cost_per_kwh))

    return energy_generated, payback_time, balances

def app():
    st.title("🌞 Balcony Solar Panel RIO Calculator 🌞")
    st.markdown("""<p>This app wil help you analyze the ideal size of solar panels, tailored for the Berlin subsidy program for mini balcony solar powerplants.
                </br>
                Given user-defined parameters and solar radiation data, it calculates various metrics, including energy generation and ROI overtime</p>.              
                """,unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Parameters")
        c1, c2 = st.columns(2)
        
        longitude = c1.number_input('Longitude', value=13.40, help="Longitude of your location in degrees. For Berlin, it's approximately 13.40.")
        latitude = c2.number_input('Latitude', value=52.52, help="Latitude of your location in degrees. For Berlin, it's approximately 52.52.")
        
        panel_price = c1.number_input('Panel Price (EUR per W)', min_value=0.0, value=0.52, help="Costs of the solar panels in EUR per Watt of nominal power.")
        installation_costs = c2.number_input('Installation Costs (EUR)', min_value=0, value=30, help="Additional costs associated with the installation of the solar panels in EUR.")
        
        energy_cost_per_kwh = st.number_input('Energy Cost per kWh (EUR)', min_value=0.0, value=0.35, help="Energy rates in EUR per kWh.")
        subsidy_amount = st.number_input('Subsidy Amount (EUR)', min_value=0, value=500, help="Subsidy amount received in EUR.")
        
        max_inverter_power = st.number_input('Max Inverter Power (W)', min_value=0, value=600, help="The maximum power output of the inverter in Watts.")
        panel_azimuth = st.slider('Panel Azimuth', min_value=0, max_value=360, value=245, help="The azimuth angle of your solar panels in degrees (0=north, 90=east, 180=south, 270=west).")
        
        panel_angle = st.slider('Panel Angle', min_value=0, max_value=90, value=90, help="The tilt angle of your solar panels in degrees (0=horizontal, 90=vertical).")
        inverter_efficiency = st.slider('Inverter Efficiency', min_value=0.0, max_value=1.0, value=0.91, help="The average efficiency of the inverter.")
        
        pv_tech = st.selectbox('PV Tech', options=['crystSi', 'CIS', 'CdTe', 'Unknown'], index=0, help="The technology of the photovoltaic cells. Options are 'crystSi', 'CIS', 'CdTe', or 'Unknown'.")
        system_losses = st.slider('System Losses', min_value=0.0, max_value=1.0, value=0.05, help="Other losses that are not associated with inverter efficiency like panels degradation, glass transmittance, dirt, and more.")
        
        unused_energy = st.slider('Unused Energy', min_value=0.0, max_value=1.0, value=0.4, help="Percentage of the energy generated that is not directly used, assuming there is no buyback.")
        horizon_data = st.multiselect('Horizon Data', options=[90, 20], default=[90, 90, 90, 20, 20, 20, 90, 90], help="List of elevation of horizon in degrees, at arbitrary number of equally spaced azimuths clockwise from north.")
        
        panel_sizes = st.multiselect('Panel Sizes (W)', options=[600, 800, 1000, 1100, 1200, 1300, 1400], default=[600, 800, 1000, 1100, 1200, 1300, 1400], help="List of the panel sizes to be analyzed in Watts.")
        
        st.divider()
        
        st.write('Author: [gniewus](https://www.linkedin.com/in/tomtkaczyk/)')

    btn = st.button('Submit','submit',type='primary',use_container_width=True)

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
        
        params_dict = {'longitude': longitude,'latitude': latitude,'panel_price': panel_price,'installation_costs': installation_costs,'energy_cost_per_kwh': energy_cost_per_kwh,'subsidy_amount': subsidy_amount,'max_inverter_power': max_inverter_power,'panel_azimuth': panel_azimuth,'panel_angle': panel_angle,'inverter_efficiency': inverter_efficiency,'pv_tech': pv_tech,'system_losses': system_losses,'unused_energy': unused_energy,'horizon_data': horizon_data,'panel_sizes': panel_sizes}
        params_df = pd.DataFrame.from_dict(params_dict,orient='index',columns=['Value']).T
        # Plot and display results
        figs = plot_results(panel_sizes, energy_generated, payback_time, balances, solar_data, max_inverter_power, panel_angle, panel_azimuth)
        report_download_btn(figs,params_df)
        st.markdown("""
            - Credits to __riparise__ fot the original repo with calculation logic: [solar-panel-sizing-tool](https://github.com/riparise/solar-panel-sizing-tool/)
            - Author: [gniewus](https://www.linkedin.com/in/tomtkaczyk/)
            """)
if __name__ == '__main__':
    app()
