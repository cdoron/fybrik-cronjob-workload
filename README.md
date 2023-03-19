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

1. Next, we wish to create an asset for reading. First, let us deploy a `FybrikModule` for reading:
   ```bash
   kubectl apply -f $FYBRIK_WORKLOAD/arrow-flight-module.yaml -n fybrik-system
   ```

1. Upload the CSV file to an object storage of your choice such as AWS S3, IBM Cloud Object Storage or Ceph. Make a note of the service endpoint, bucket name, and access credentials. You will need them later.

    ??? tip "Setup and upload to localstack"

    For experimentation you can install localstack to your cluster instead of using a cloud service.

    1. Define variables for access key and secret key
       ```bash
       export ACCESS_KEY="myaccesskey"
       export SECRET_KEY="mysecretkey"
       ```
    1. Install localstack to the currently active namespace and wait for it to be ready:
       helm repo add localstack-charts https://localstack.github.io/helm-charts
       helm install localstack localstack-charts/localstack \
              --set startServices="s3" \
              --set service.type=ClusterIP \
              --set livenessProbe.initialDelaySeconds=25
       kubectl wait --for=condition=ready --all pod -n fybrik-notebook-sample --timeout=120s
    1. Create a port-forward to communicate with localstack server:
      ```bash
      kubectl port-forward svc/localstack 4566:4566 &
      ```
    1. Use [AWS CLI](https://aws.amazon.com/cli/) to upload the dataset to a new created bucket in the localstack server:
      ```bash
      export ENDPOINT="http://127.0.0.1:4566"
      export BUCKET="demo"
      export OBJECT_KEY="PS_20174392719_1491204439457_log.csv"
      export FILEPATH=$FYBRIK_DIR/samples/notebook/PS_20174392719_1491204439457_log.csv
      export REGION=theshire
      aws configure set aws_access_key_id ${ACCESS_KEY} && aws configure set aws_secret_access_key ${SECRET_KEY}
      aws configure set region ${REGION}
      aws --endpoint-url=${ENDPOINT} s3api create-bucket --bucket ${BUCKET} --region ${REGION} --create-bucket-configuration LocationConstraint=${REGION}
      aws --endpoint-url=${ENDPOINT} s3api put-object --bucket ${BUCKET} --key ${OBJECT_KEY} --body ${FILEPATH}
      ```

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
   kubectl apply -f $FYBRIK_WORKLOAD/rbac.yaml
   ```

1. At this point, everything should be in place. We have the assets, `FyrbikModule`-s, governance policy. We are ready to run a workload job. This job creates a `FybrikApplication`, waits for that `FybrikApplication` to be ready, run the workload that reads from one asset and writes to another, and finally deletes the `FybrikApplication`:
   ```bash
   kubectl apply -f $FYBRIK_WORKLOAD/job.yaml
   ```

1. To verify that the dataset has been written, run:
   ```bash
   kubectl delete pod mysql-client --ignore-not-found=true
   kubectl run mysql-client --rm --tty -i --restart='Never' --image  docker.io/bitnami/mysql:8.0.32-debian-11-r0 --namespace fybrik-airbyte-sample --env MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD --command -- bash
   mysql -h mysql.fybrik-airbyte-sample.svc.cluster.local -uroot -p"$MYSQL_ROOT_PASSWORD"
   ```

1. In a mysql client shell prompt insert the following commands to show the newly created dataset:
   ```bash
   use test;
   show tables;
   select * from demo;
   ```
