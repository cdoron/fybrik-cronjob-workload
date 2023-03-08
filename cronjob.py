import json
import sys
import time

from kubernetes import config, dynamic
from kubernetes.client import api_client, ApiException
from kubernetes import client as k8s_client
from fybrikapplication import get_fybrikapplication_dict

def struct_to_endpoint(endpoint):
    endpoint_struct = endpoint[endpoint["name"]]
    return "{}://{}:{}".format(endpoint_struct["scheme"], endpoint_struct["hostname"],
                               endpoint_struct["port"])


def wait_for_fybrikapplication_to_be_ready(custom_object_api):
    while True:
        try:
            fybrikapplication = custom_object_api.get_namespaced_custom_object(
                group="app.fybrik.io", version="v1beta1",
                namespace="fybrik-workload", plural="fybrikapplications",
                name="my-app"
            )
        except ApiException:
            print("FybrikApplication not found")
            time.sleep(1)
            continue

        if "status" not in fybrikapplication or \
            "ready" not in fybrikapplication["status"] or \
            not fybrikapplication["status"]["ready"]:
            print("FybrikApplication not ready")
            time.sleep(1)
            continue

        assets_ready = True
        endpoints = {}
        for name, asset in fybrikapplication["status"]["assetStates"].items():
            for condition in asset["conditions"]:
                if condition["type"] == "Ready":
                    if condition["status"] == 'True':
                        endpoints[name] = struct_to_endpoint(asset["endpoint"])
                    else:
                        print("asset not ready")
                        assets_ready = False
                        break

        if not assets_ready:
            time.sleep(1)
            continue

        return endpoints


def create_fybrik_application(client, fa_dict):
    fybrikapplication_api = client.resources.get(
        api_version="app.fybrik.io/v1beta1", kind="FybrikApplication"
    )

    fybrikapplication_api.create(fa_dict)


def main(args):
    client = dynamic.DynamicClient(
        # api_client.ApiClient(configuration=config.load_kube_config())
        api_client.ApiClient(configuration=config.load_incluster_config())
    )

    read_asset_name = args[0]
    fa_dict = get_fybrikapplication_dict(read_asset_name)
    create_fybrik_application(client, fa_dict)

    custom_object_api = k8s_client.CustomObjectsApi()

    endpoints = wait_for_fybrikapplication_to_be_ready(custom_object_api)
    print(str(endpoints))


if __name__ == "__main__":
    main(sys.argv[1:])
