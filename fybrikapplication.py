import json

fybrik_application_str = '''
{
    "apiVersion": "app.fybrik.io/v1beta1",
    "kind": "FybrikApplication",
    "metadata": {
        "labels": {
            "app": "my-app"
        },
        "name": "my-app",
        "namespace": "fybrik-airbyte-sample"
    },
    "spec": {
        "appInfo": {
            "intent": "Fraud Detection"
        },
        "data": [
            {
                "dataSetID": "openmetadata-https.default.openmetadata.userdata",
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
'''

def get_fybrikapplication_dict():
    return json.loads(fybrik_application_str)