# Berlin's Balcony Solar Panel Sizing Streamlit App ☀️

The Solar Panel Sizing Streamlit App is an interactive tool designed to assist users in analyzing the ideal size of solar panels for their specific needs, with a focus on mini balcony solar power plants. This app is tailored to the Berlin subsidy program, which restricts the inverter power to 600 watts. 🏙️

This app calculates various metrics, including energy generation and payback time, based on user-defined parameters and solar radiation data, providing insights to optimize your solar power setup. 📊

## Acknowledgments

- The calculation logic is based on the [Solar Panel Sizing App](https://github.com/gniewus/solar-panel-sizing-app/) repository.
- Radiation data is taken from the [European Photovoltaic Geographical Information System](https://re.jrc.ec.europa.eu/api/v5_2/) using the [pvlib](https://pvlib-python.readthedocs.io/en/stable/) library.

## Development

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/YourUsername/solar-panel-sizing-streamlit-app.git
   ```

2. Change to the project directory:

   ```bash
   cd solar-panel-sizing-streamlit-app
   ```

3. Install the required Python packages using `pip`:

   ```bash
   pip install -r requirements.txt
   ```

## Usage 🧰

To run the Solar Panel Sizing Streamlit App, use the following command:

   ```bash
   streamlit run app.py
   ```

Navigate to the address provided in the terminal to interact with the app. Use the input widgets to modify parameters like latitude, longitude, panel azimuth, panel angle, and more, according to your specific setup and requirements.

After modifying the parameters, click the "Submit" button to run the calculations and visualize the results interactively.

## Output 📈

The app generates three interactive plots to help you analyze your solar panel sizing:

1. **Average Hourly Energy Generation per kW of installed solar panels:** This plot shows the average historical solar generation (per kW of installed solar panel) throughout the day, categorized by seasons (Winter, Spring, Summer, Fall).

2. **Energy Generation and payoff time vs. panel size:** This plot illustrates the relationship between panel size and energy generation per year, along with the payback time.

3. **Return over time vs. panel size:** This plot displays the balance evolution in euros for different panel sizes, allowing you to compare the financial aspects of your solar power plant.

## License 📜

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Feel free to leave any comments, suggestions, or open merge requests.
