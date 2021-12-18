# Virtuso on GCP: _Faster_ with Container-Optimised OS

## Requirements

- [GCP Account](https://cloud.google.com)
- Development environment with following commands:
  - [Docker](https://www.docker.com)
    - how to install: https://docs.docker.com/get-docker
  - [`gcloud`](https://cloud.google.com/sdk/gcloud)
    - how to install: https://cloud.google.com/sdk/docs/install
  - [`gsutil`](https://cloud.google.com/storage/docs/gsutil)
    - how to install: https://cloud.google.com/storage/docs/gsutil_install

## Overview

0. Prepare your [configurations](https://github.com/Ningensei848/virtuoso-on-gcp-with-cos#0-configuration)
1. Run `virtuoso` container on your local and Load your rdf data
2. Upload `virtuoso.db` to GCS via `gsutil` command
3. Create and Auto-Start your instance via `gcloud` command
4. Congratulations 🎉🎉🥳🎉🎉🥳🎉

## Usage

### 0. Configuration

- Setup on GCP
- Install `gcloud` and `gsutil` command
- Reserve static external IP address
- Get your domain
- Edit `.env` file

#### Setup on GCP

- [Create account](https://console.cloud.google.com/freetrial)
- [Create project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)

<details>
<summary>how to install `gcloud` and `gsutil` command</summary>

Other distributions [here](https://cloud.google.com/sdk/docs/install#installation_instructions):

for Ubuntu:

```shell
sudo apt-get install apt-transport-https ca-certificates gnupg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-sdk
```

```shell
gcloud init
```

</details>

#### Reserve static external IP address

cf. https://cloud.google.com/compute/docs/ip-addresses/reserve-static-external-ip-address

#### Get your domain

cf. [Search results in google](https://www.google.com/search?q=gcp+how+to+get+domain)

#### Edit `.env` file

Referring to `.env.example`, rewrite your `.env`

<details>
<summary>more info ...</summary>

Mandatory:

- `USERNAME`: your username
- `USER_EMAIL`: your email (for letsencrypt)
- `SERVER_NAME`: your domain (e.g. your-doma.in)
- `GCP_PROJECT_NAME`: your project name
- `GCE_*`: instance preferences your want to create
- `GCS_BUCKET_NAME`: your bucket name

Optional:

- `Parameters_NumberOfBuffers` & `Parameters_MaxDirtyBuffers`: virtuoso performance tuning
- `TOKEN_LINE`: enable notifycation cf. https://notify-bot.line.me

</details>

### 1. load RDF data

virtuoso official documentation: http://docs.openlinksw.com/virtuoso/rdfperfloading/

1. Put the RDF data under `data/`
2. Config from `.env`: `source .env`
3. Run script: `docker run --rm -v $(pwd)/data:/data -v $(pwd)/script:/script -u "$(id -u $USERNAME):$(id -g $USERNAME)" python:3.10-alpine python /script/configureSQL.py ttl --origin https://$SERVER_NAME`
4. Start virtuoso container: `docker-compose up -d virtuoso`

- confirm your server online: `docker-compose logs`
- > virtuoso_container | HH:MM:SS Server online at `$PORT_VIRTUOSO_ISQL` (pid 1)

5. Load RDF data on virtuoso: `nohup docker exec -i virtuoso_container isql $PORT_VIRTUOSO_ISQL -U dba -P $PASSWORD_VIRTUOSO < ./script/initialLoader.sql &`

- `nohup $@ &` runs commands (`$@`) in the background and independently.
- To check the completion of the process, please refer to `nohup.out`.

### 2. Upload `virtuoso.db` to GCS by `gsutil`

1. Create a named bucket with the command `gsutil mb gs://<bucketname>`

- You can use the `-p` option to link it to your project

2. Copy data from the local to the GCS: `gsutil cp src_url dst_url`

```shell
source .env
gsutil mb -p $GCE_PROJECT_NAME gs://$GCS_BUCKET_NAME
gsutil cp ./.virtuoso/virtuoso.db gs://$GCS_BUCKET_NAME
```

### 3. Create instance by `gcloud`

For variable `GCE_CREATE_ARGS`, check the description in `.env.example` carefully and read the GCP documentation _much carefully_ before executing commands below.

```shell
source .env
gcloud compute instances create $GCE_CREATE_ARGS
```

<details>
<summary>Learn more</summary>

When we create an instance with `gcloud`, the following arguments are given:

```shell
GCE_CREATE_ARGS="$GCE_INSTANCE_NAME \
 --project $GCE_PROJECT_NAME \
 --zone $GCE_ZONE \
 --machine-type $GCE_MACHINE_TYPE \
 --tags $GCE_TAGS \
 --create-disk $GCE_CREATE_DISK \
 --metadata-from-file user-data=$PWD/gcp/cloud-config.yml,NGINX_CONFIG=$PWD/nginx/default.conf.template,DOTENV=$PWD/.env,COMPOSE_FILE=$PWD/docker-compose.yml,startup-script=$PWD/gcp/startup.sh \
 --metadata google-logging-enabled=true,cos-metrics-enabled=true,USERNAME=$USERNAME \
 --address $GCE_STATIC_IP_ADDRESS \
 --shielded-secure-boot \
 --shielded-vtpm \
 --shielded-integrity-monitoring"
```

In this case, `metadata-from-file` and `metadata` are used to send various files to GCP.

- `cloud-config.yml`: Read only once when the instance is created
- `startup.sh`: Loaded every time in start up (from a stopped)
  - `.env`, `default.conf.template`, `docker-compose.yml` are read from the metadata server and saved as a file
  - Also synchronize data with `gsutil` and launch containers with `docker-compose`.

</details>

### 4. complete !

Congratulations !!

Open the GCP project page and check that the instance has been successfully launched.

## Future work

- with GitHub Actions: for example, if there is a change under `data/` in the repository, it should trigger the virtuoso container to start → load the data → sync with GCS

## LICENSE

[_MIT_](https://github.com/Ningensei848/virtuoso-on-gcp-with-cos/blob/main/LICENSE)
