# fybrik-workload-job

Before we begin, let us set environment variables representing copies of the different repositories that we need. For example:
```bash
git clone https://github.com/cdoron/fybrik-workload-job /tmp/fybrik-workload-job
git clone https://github.com/fybrik/fybrik /tmp/fybrik
git clone https://github.com/fybrik/airbyte-module /tmp/airbyte-module

export FYBRIK_WORKLOAD=/tmp/fybrik-workload-job
export FYBRIK_DIR=/tmp/fybrik
export AIRBYTE_MODULE_DIR=/tmp/airbyte-module
```

## Read and Write Workload Sample

1. Follow the steps for [Writing Dataset with Fybrik Application](https://github.com/fybrik/airbyte-module/blob/main/fybrik/README_mysql.md) until step 8. In step 8, run the first command (`Asset` creation), but not the second (`FybrikApplication` creation).

1. At this point, we have an asset for writing, as well as a `FybrikModule` for writing MySQL datasets.

1. Next, let us create an asset for reading, and deploy a `FybrikModule` for reading. If the `arrow-flight-module` is not yet deployed, deploy it now:
   ```bash
   kubectl apply -f https://github.com/fybrik/arrow-flight-module/releases/download/v0.11.0/module.yaml -n fybrik-system   
   ```

1. Follow the instructions in [Notebook sample for the read flow](https://fybrik.io/v1.3/samples/notebook-read/) to deploy an S3 service. Replace `fybrik-notebook-sample` with `fybrik-airbyte-sample`.

1. run:
   ```bash
   cat << EOF | kubectl apply -f -
   apiVersion: v1
   kind: Secret
   metadata:
     name: paysim-csv
   type: Opaque
   stringData:
     access_key: "${ACCESS_KEY}"
     secret_key: "${SECRET_KEY}"
   EOF
   ```
   Next, register the data asset itself in the data catalog. We use port-forwarding to send asset creation requests to the Katalog connector.
   ```bash
   cat << EOF | kubectl apply -f -
   apiVersion: katalog.fybrik.io/v1alpha1
   kind: Asset
   metadata:
     name: paysim-csv
   spec:
     secretRef:
       name: paysim-csv
     details:
       dataFormat: csv
       connection:
         name: s3
         s3:
           endpoint: "http://localstack.fybrik-airbyte-sample.svc.cluster.local:4566"
           bucket: "demo"
           object_key: "PS_20174392719_1491204439457_log.csv"
     metadata:
       name: Synthetic Financial Datasets For Fraud Detection
       geography: theshire
       tags:
         Purpose.finance: true
       columns:
         - name: nameOrig
           tags:
             PII.Sensitive: true
         - name: oldbalanceOrg
           tags:
             PII.Sensitive: true
         - name: newbalanceOrig
           tags:
             PII.Sensitive: true
   EOF
   CATALOGED_ASSET="fybrik-airbyte-sample/paysim-csv"
   ```

1. Before creating the governance policy, make sure that there is no other policy with the same name:
   ```bash
   kubectl delete cm sample-policy -n fybrik-system --ignore-not-found=true
   ```

1. Create a file named `sample-policy.rego` with the following contents:
   ```bash
   package dataapi.authz

   rule[{"action": {"name":"RedactAction", "columns": column_names}, "policy": description}] {
     description := "Redact columns tagged as PII.Sensitive in datasets tagged with Purpose.finance = true"
     input.action.actionType == "read"
     input.resource.metadata.tags["Purpose.finance"]
     column_names := [input.resource.metadata.columns[i].name | input.resource.metadata.columns[i].tags["PII.Sensitive"]]
     count(column_names) > 0
   }
   ```

1. Run:
   ```bash
   kubectl -n fybrik-system create configmap sample-policy --from-file=sample-policy.rego
   kubectl -n fybrik-system label configmap sample-policy openpolicyagent.org/policy=rego
   while [[ $(kubectl get cm sample-policy -n fybrik-system -o 'jsonpath={.metadata.annotations.openpolicyagent\.org/policy-status}') != '{"status":"ok"}' ]]; do echo "waiting for policy to be applied" && sleep 5; done
   ```

1. Create a namespace called `fybrik-workload`. Our workload creates and deletes FybrikApplications, so we need to grant workloads running in `fybrik-workload` proper permission:
   ```bash
   kubectl create ns fybrik-workload
   kubectl apply -f rbac.yaml
   ```
