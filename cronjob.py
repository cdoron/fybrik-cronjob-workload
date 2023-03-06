import json

from kubernetes import config, dynamic
from kubernetes.client import api_client
from kubernetes import client as k8s_client


def main():
    dynamic.DynamicClient(
        api_client.ApiClient(configuration=config.load_kube_config())
    )

    custom_object_api = k8s_client.CustomObjectsApi()

    fybrikapplication = custom_object_api.get_namespaced_custom_object(
        group="app.fybrik.io", version="v1beta1",
        namespace="fybrik-airbyte-sample", plural="fybrikapplications",
        name="my-app"
    )

    print(str(json.dumps(fybrikapplication)))


if __name__ == "__main__":
    main()
