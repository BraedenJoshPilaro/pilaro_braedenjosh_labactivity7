import argparse
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests


# World Bank indicator:
# SP.DYN.LE00.IN = Life expectancy at birth, total (years)
INDICATOR_CODE = "SP.DYN.LE00.IN"
INDICATOR_NAME = "Life expectancy at birth (years)"

SUPPORTED_COUNTRIES = {
    "PHL": "Philippines",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "THA": "Thailand",
    "VNM": "Vietnam",
    "SGP": "Singapore",
}


def parse_arguments():
    """Read optional settings supplied through the command line."""
    parser = argparse.ArgumentParser(
        description=(
            "Retrieve life expectancy data from the World Bank API "
            "and create an interactive visualization."
        )
    )

    parser.add_argument(
        "--countries",
        nargs="+",
        default=["PHL", "IDN", "MYS", "THA", "VNM", "SGP"],
        help="Country codes separated by spaces.",
    )

    parser.add_argument(
        "--start-year",
        type=int,
        default=2000,
        help="First year included in the analysis.",
    )

    parser.add_argument(
        "--end-year",
        type=int,
        default=2023,
        help="Last year included in the analysis.",
    )

    parser.add_argument(
        "--name",
        default="life_expectancy",
        help="Base name used for generated output files.",
    )

    return parser.parse_args()


def validate_inputs(countries, start_year, end_year):
    """Validate country codes and year arguments."""
    normalized_countries = [country.upper() for country in countries]

    invalid_countries = [
        country
        for country in normalized_countries
        if country not in SUPPORTED_COUNTRIES
    ]

    if invalid_countries:
        valid_codes = ", ".join(SUPPORTED_COUNTRIES.keys())
        invalid_codes = ", ".join(invalid_countries)
        raise ValueError(
            f"Unsupported country code(s): {invalid_codes}. "
            f"Supported codes are: {valid_codes}."
        )

    if start_year > end_year:
        raise ValueError(
            "The start year cannot be greater than the end year."
        )

    if start_year < 1960:
        raise ValueError(
            "The World Bank time series used in this activity "
            "begins in 1960."
        )

    return normalized_countries


def fetch_world_bank_data(countries, start_year, end_year):
    """Retrieve life expectancy records from the World Bank API."""
    country_parameter = ";".join(countries)

    url = (
        f"https://api.worldbank.org/v2/country/{country_parameter}"
        f"/indicator/{INDICATOR_CODE}"
    )

    parameters = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 2000,
    }

    print("Connecting to the World Bank API...")
    print(f"Countries: {', '.join(countries)}")
    print(f"Year range: {start_year}-{end_year}")

    try:
        response = requests.get(
            url,
            params=parameters,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise ConnectionError(
            f"Unable to retrieve data from the World Bank API: {error}"
        ) from error

    try:
        response_data = response.json()
    except ValueError as error:
        raise ValueError(
            "The World Bank API did not return valid JSON data."
        ) from error

    if not isinstance(response_data, list) or len(response_data) < 2:
        raise ValueError(
            "The World Bank API returned an unexpected response."
        )

    records = response_data[1]

    if not records:
        raise ValueError(
            "The API returned no records for the selected settings."
        )

    return records


def process_records(records):
    """Convert raw API records to a clean Pandas DataFrame."""
    cleaned_records = []

    for record in records:
        value = record.get("value")

        # Missing observations from the API are represented by None.
        if value is None:
            continue

        cleaned_records.append(
            {
                "Country": record["country"]["value"],
                "Country Code": record["countryiso3code"],
                "Year": int(record["date"]),
                "Life Expectancy": float(value),
            }
        )

    if not cleaned_records:
        raise ValueError(
            "No non-missing observations were found in the API response."
        )

    dataframe = pd.DataFrame(cleaned_records)

    dataframe = (
        dataframe.drop_duplicates(
            subset=["Country Code", "Year"]
        )
        .sort_values(["Country", "Year"])
        .reset_index(drop=True)
    )

    return dataframe


def create_summary(dataframe):
    """Calculate descriptive statistics for each country."""
    summary = (
        dataframe.groupby("Country")["Life Expectancy"]
        .agg(
            First_Year_Value="first",
            Latest_Year_Value="last",
            Mean="mean",
            Minimum="min",
            Maximum="max",
            Observations="count",
        )
        .reset_index()
    )

    summary["Change"] = (
        summary["Latest_Year_Value"]
        - summary["First_Year_Value"]
    )

    numeric_columns = [
        "First_Year_Value",
        "Latest_Year_Value",
        "Mean",
        "Minimum",
        "Maximum",
        "Change",
    ]

    summary[numeric_columns] = summary[numeric_columns].round(2)

    return summary


def create_interactive_chart(dataframe, output_path):
    """Create and save an interactive Plotly line visualization."""
    figure = px.line(
        dataframe,
        x="Year",
        y="Life Expectancy",
        color="Country",
        markers=True,
        title=(
            "Life Expectancy Trends in Selected "
            "Southeast Asian Countries"
        ),
        labels={
            "Year": "Year",
            "Life Expectancy": "Life Expectancy at Birth (Years)",
            "Country": "Country",
        },
        hover_data={
            "Country Code": True,
            "Year": True,
            "Life Expectancy": ":.2f",
        },
    )

    figure.update_layout(
        template="plotly_white",
        title_x=0.5,
        hovermode="x unified",
        legend_title_text="Country",
        xaxis=dict(dtick=2),
    )

    figure.write_html(
        output_path,
        include_plotlyjs=True,
        full_html=True,
    )


def save_summary_report(summary, output_path):
    """Save a short text interpretation of the results."""
    highest_country = summary.loc[
        summary["Latest_Year_Value"].idxmax()
    ]
    greatest_change = summary.loc[
        summary["Change"].idxmax()
    ]

    report_lines = [
        "WORLD BANK LIFE EXPECTANCY ANALYSIS",
        "=" * 50,
        "",
        "Summary statistics:",
        summary.to_string(index=False),
        "",
        "Interpretation:",
        (
            f"1. {highest_country['Country']} had the highest latest "
            f"available life expectancy in the selected data at "
            f"{highest_country['Latest_Year_Value']:.2f} years."
        ),
        (
            f"2. {greatest_change['Country']} recorded the largest "
            f"change across the selected period at "
            f"{greatest_change['Change']:.2f} years."
        ),
        (
            "3. Differences among countries can be examined by "
            "hovering over lines and data points in the HTML chart."
        ),
        "",
        "Source: World Bank Indicators API",
        f"Indicator: {INDICATOR_CODE} - {INDICATOR_NAME}",
    ]

    output_path.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )


def main():
    """Run the complete API, processing, and visualization workflow."""
    arguments = parse_arguments()

    try:
        countries = validate_inputs(
            arguments.countries,
            arguments.start_year,
            arguments.end_year,
        )

        records = fetch_world_bank_data(
            countries,
            arguments.start_year,
            arguments.end_year,
        )

        dataframe = process_records(records)
        summary = create_summary(dataframe)

        project_root = Path(__file__).resolve().parent.parent
        data_directory = project_root / "data"
        output_directory = project_root / "outputs"

        data_directory.mkdir(exist_ok=True)
        output_directory.mkdir(exist_ok=True)

        csv_path = data_directory / f"{arguments.name}_data.csv"
        chart_path = output_directory / f"{arguments.name}_chart.html"
        summary_path = output_directory / f"{arguments.name}_summary.txt"

        dataframe.to_csv(csv_path, index=False)
        create_interactive_chart(dataframe, chart_path)
        save_summary_report(summary, summary_path)

        print("\nData retrieval and processing completed.")
        print(f"Valid observations: {len(dataframe)}")
        print("\nSummary statistics:")
        print(summary.to_string(index=False))

        print("\nGenerated files:")
        print(f"CSV dataset: {csv_path}")
        print(f"Interactive chart: {chart_path}")
        print(f"Summary report: {summary_path}")

        print(
            "\nOpen the HTML chart in a web browser "
            "to explore the visualization."
        )

    except (
        ValueError,
        ConnectionError,
        OSError,
    ) as error:
        print(f"\nERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()