import json
import pyarrow.flight as fl
import pandas as pd


def run_workload(read_asset_name, endpoints):
    endpoint = endpoints[read_asset_name]
    # Create a Flight client
    client = fl.connect(endpoint)

    # Prepare the request
    request = {
        "asset": read_asset_name,
        # To request specific columns add to the request a "columns" key with a list of column names
        # "columns": [...]
    }

    # Send request and fetch result as a pandas DataFrame
    info = client.get_flight_info(fl.FlightDescriptor.for_command(json.dumps(request)))
    reader: fl.FlightStreamReader = client.do_get(info.endpoints[0].ticket)
    df: pd.DataFrame = reader.read_pandas()
    print(df)
