"""
Shared  data preparation for  notebooks and mapping of fuel and canton categories.
"""

import pandas as pd

# Fuel mapping to summarized categories for plotting
fuel_groups = {
    "Battery electric vehicle (BEV)": "BEV",
    "Petrol: conventional": "Petrol",
    "Diesel: conventional": "Diesel",
    "Petrol: hybrid electric vehicle (HEV)": "Hybrid",
    "Diesel: hybrid electric vehicle (HEV)": "Hybrid",
    "Plug-in hybrid electric vehicle (PHEV): petrol": "Hybrid",
    "Plug-in hybrid electric vehicle (PHEV): diesel": "Hybrid",
    "Fuel cell electric vehicle (FCEV)": "Other", # Hydrogen car
    "Gas (mono- and bi-fuel)": "Other",
    "Other": "Other",
}


# Canton mapping to short codes 
canton_short = {
    "Zurich": "ZH", "Bern": "BE", "Lucerne": "LU", "Uri": "UR",
    "Schwyz": "SZ", "Obwalden": "OW", "Nidwalden": "NW", "Glarus": "GL",
    "Zug": "ZG", "Fribourg": "FR", "Solothurn": "SO", "Basel-Stadt": "BS",
    "Basel-Landschaft": "BL", "Schaffhausen": "SH",
    "Appenzell Ausserrhoden": "AR", "Appenzell Innerrhoden": "AI",
    "St. Gallen": "SG", "Graubünden": "GR", "Aargau": "AG", "Thurgau": "TG",
    "Ticino": "TI", "Vaud": "VD", "Valais": "VS", "Neuchâtel": "NE",
    "Geneva": "GE", "Jura": "JU",
}

# BFS numbers used by the official swisstopo API
canton_bfs = {
    "Zurich": 1, "Bern": 2, "Lucerne": 3, "Uri": 4, "Schwyz": 5,
    "Obwalden": 6, "Nidwalden": 7, "Glarus": 8, "Zug": 9, "Fribourg": 10,
    "Solothurn": 11, "Basel-Stadt": 12, "Basel-Landschaft": 13,
    "Schaffhausen": 14, "Appenzell Ausserrhoden": 15,
    "Appenzell Innerrhoden": 16, "St. Gallen": 17, "Graubünden": 18,
    "Aargau": 19, "Thurgau": 20, "Ticino": 21, "Vaud": 22,
    "Valais": 23, "Neuchâtel": 24, "Geneva": 25, "Jura": 26,
}



class PreparSwissVehicle:
    """
    prepare in-use vehicle registration CSV for plotting. 

    Attributes:
        df: cleaned raw DataFrame (all years, all cantons)
        latest_year: most recent year present in the data
        
    """

    category_order = ["BEV", "Petrol", "Diesel", "Hybrid", "Other"]

    def __init__(self, csv_path="../data/registered.csv"):
        self.df = pd.read_csv(csv_path, sep=";")
        self._prepare()

    def _prepare(self):
        """Filters to passenger cars and cleans up columns."""
        # Drop not needed columns
        self.df.drop(columns=["Type of holder"], errors="ignore", inplace=True)

        # Prepare year column
        self.df.rename(columns={"TIME_PERIOD": "YEAR"}, inplace=True)
        self.df["YEAR"] = self.df["YEAR"].astype(int)

        # Filter to passenger cars only
        self.df = self.df[self.df["Vehicle group / type"].isin(["Passenger car", "Passenger cars"])]
        self.df.drop(columns=["Vehicle group / type"], inplace=True)

        # Drop total and Switzerland rows
        self.df = self.df[~self.df["Canton"].isin(["Total", "Switzerland", "Schweiz"])]

    @property
    def latest_year(self):
        """Returns the most recent year present in the loaded data."""
        return int(self.df["YEAR"].max())

    def _aggregate(self, df, group_cols):
        """Returns OBS_VALUE summed over group_cols after mapping fuels to categories."""
        df = df[df["Fuel"] != "Total"]

        # we fill missing fuel types with "Other" to avoid dropping rows with missing fuel info
        df = df.assign(FuelCategory=df["Fuel"].map(fuel_groups).fillna("Other"))

        return df.groupby(group_cols, as_index=False)["OBS_VALUE"].sum()

    def aggregate_by_year(self):
        """Returns registrations grouped by YEAR and FuelCategory."""
        return self._aggregate(self.df, ["YEAR", "FuelCategory"])

    def aggregate_by_canton(self, target_year=None):
        """Returns registrations grouped by canton and fuel type.
        
        Return: Canton and total registrations for each fuel category
                | Canton | FuelCategory | OBS_VALUE |
                |--------|--------------|-----------|
                | ZH     | BEV          | 100       |
                | ZH     | Petrol       | 500       |
                | AG     | BEV          | 50        | 
        """

        if target_year is None:
            target_year = self.latest_year

        return self._aggregate(self.df[self.df["YEAR"] == target_year], ["Canton", "FuelCategory"])

    def current_year_pivot(self):
        """Returns a DataFrame with cantons and fuel categories as columns for the latest year 
        

        Return: Example output for the latest year (e.g., 2023):
                | Canton | BEV | Petrol | Diesel | Hybrid | Other |
                |--------|-----|--------|--------|--------|-------|
                | ZH     | 100 | 500    | 300    | 200    | 50    |
        
        """
        return self.to_pivot(self.aggregate_by_canton(), "Canton")

    def to_pivot(self, df, index_col):
        """Pivots a grouped DataFrame into wide format ordered by category_order.
        
        Needed for current year and `a_fuel_over_time.ipynb.`"""
        pivot = df.pivot(index=index_col, columns="FuelCategory", values="OBS_VALUE")
        pivot = pivot.reindex(columns=self.category_order)
        return pivot.fillna(0)


