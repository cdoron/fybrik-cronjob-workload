import json
import pyarrow.flight as fl
import pyarrow as pa


def run_workload(read_asset_name, write_asset_name, endpoints):
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
    table: pa.Table = reader.read_all()
    print(table.to_pandas())

    print("Now let us try to write")
    endpoint = endpoints[write_asset_name]
    client = fl.connect(endpoint)

    request = {
        "asset": write_asset_name,
        "json_schema": '{"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",  "properties": {"step": { "type": ["null", "string"] }, "type": { "type": ["null", "string"] }, "amount": { "type": ["null", "string"] }, "nameOrig": { "type": ["null", "string"] }, "oldbalanceOrg": { "type": ["null", "string"] }, "newbalanceOrig": { "type": ["null", "string"] }, "nameDest": { "type": ["null", "string"] }, "oldbalanceDest": { "type": ["null", "string"] }, "newbalanceDest": { "type": ["null", "string"] }, "isFraud": { "type": ["null", "string"] }, "isFlaggedFraud": { "type": ["null", "string"] }, "copied_column": { "type": ["null", "string"] } }}',
    }

    writer, _ = client.do_put(fl.FlightDescriptor.for_command(json.dumps(request)),
                              table.schema)
    writer.write_table(table)
    writer.close()
    print("Write complete")
