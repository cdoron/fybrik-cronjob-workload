import json
from string import Template

fybrik_application_str = Template('''
{
    "apiVersion": "app.fybrik.io/v1beta1",
    "kind": "FybrikApplication",
    "metadata": {
        "labels": {
            "app": "my-app"
        },
        "name": "my-app",
        "namespace": "fybrik-workload"
    },
    "spec": {
        "appInfo": {
            "intent": "Fraud Detection"
        },
        "data": [
            {
                "dataSetID": "${read_asset_name}",
                "requirements": {
                    "interface": {
                        "protocol": "fybrik-arrow-flight"
                    }
                }
            }
        ],
        "selector": {
            "workloadSelector": {
                "matchLabels": {
                    "app": "my-app"
                }
            }
        }
    }
}
''')

def get_fybrikapplication_dict(read_asset_name):
    return json.loads(fybrik_application_str.substitute(read_asset_name=read_asset_name))
