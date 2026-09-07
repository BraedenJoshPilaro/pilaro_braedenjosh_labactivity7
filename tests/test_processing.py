import sys
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIRECTORY = PROJECT_ROOT / "src"

sys.path.insert(0, str(SOURCE_DIRECTORY))

from world_bank_visualizer import (
    create_summary,
    process_records,
    validate_inputs,
)


def test_valid_inputs():
    result = validate_inputs(
        ["phl", "IDN", "vnm"],
        2010,
        2023,
    )

    assert result == ["PHL", "IDN", "VNM"]


def test_invalid_country_code():
    with pytest.raises(ValueError):
        validate_inputs(
            ["PHL", "XYZ"],
            2010,
            2023,
        )


def test_invalid_year_range():
    with pytest.raises(ValueError):
        validate_inputs(
            ["PHL"],
            2023,
            2010,
        )


def test_process_records_removes_missing_values():
    sample_records = [
        {
            "country": {"value": "Philippines"},
            "countryiso3code": "PHL",
            "date": "2020",
            "value": 72.1,
        },
        {
            "country": {"value": "Philippines"},
            "countryiso3code": "PHL",
            "date": "2021",
            "value": None,
        },
    ]

    result = process_records(sample_records)

    assert len(result) == 1
    assert result.iloc[0]["Year"] == 2020
    assert result.iloc[0]["Life Expectancy"] == 72.1


def test_create_summary():
    sample_dataframe = pd.DataFrame(
        {
            "Country": [
                "Philippines",
                "Philippines",
            ],
            "Country Code": [
                "PHL",
                "PHL",
            ],
            "Year": [
                2000,
                2020,
            ],
            "Life Expectancy": [
                70.0,
                72.5,
            ],
        }
    )

    result = create_summary(sample_dataframe)

    assert len(result) == 1
    assert result.iloc[0]["Change"] == 2.5
    assert result.iloc[0]["Mean"] == 71.25