import json
import time

from kubernetes import config, dynamic
from kubernetes.client import api_client, ApiException
from kubernetes import client as k8s_client


def struct_to_endpoint(endpoint):
    endpoint_struct = endpoint[endpoint["name"]]
    return "{}://{}:{}".format(endpoint_struct["scheme"], endpoint_struct["hostname"],
                               endpoint_struct["port"])


def wait_for_fybrikapplication_to_be_ready(custom_object_api):
    while True:
        try:
            fybrikapplication = custom_object_api.get_namespaced_custom_object(
                group="app.fybrik.io", version="v1beta1",
                namespace="fybrik-airbyte-sample", plural="fybrikapplications",
                name="my-app"
            )
        except ApiException:
            print("FybrikApplication not found")
            time.sleep(1)
            continue

        if not fybrikapplication["status"]["ready"]:
            print("FybrikApplication not ready")
            time.sleep(1)
            continue

        assetsReady = True
        endpoints = {}
        for name, asset in fybrikapplication["status"]["assetStates"].items():
            for condition in asset["conditions"]:
                if condition["type"] == "Ready":
                    if condition["status"] == 'True':
                        endpoints[name] = struct_to_endpoint(asset["endpoint"])
                    else:
                        print("asset not ready")
                        assetsReady = False
                        break

        if not assetsReady:
            time.sleep(1)
            continue

        return endpoints


def main():
    dynamic.DynamicClient(
        api_client.ApiClient(configuration=config.load_kube_config())
    )

    custom_object_api = k8s_client.CustomObjectsApi()

    endpoints = wait_for_fybrikapplication_to_be_ready(custom_object_api)
    print(str(endpoints))


if __name__ == "__main__":
    main()
