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

0. [各種必要な設定]()を整える
1. ローカル環境に virtuoso コンテナを建て，必要な RDF データをロードする
2. 得られた `virtuoso.db` を `gsutil` コマンドで GCS にアップロードする
3. `gcloud` コマンドでインスタンスを起動
4. 完成！

一番時間がかかるのは「必要な RDF データをロード」するところ（ローカル計算機のパフォーマンス依存なので）

## Usage

### 0. Configuration

#### edit & load `.env` file

`.env.example` を参考に，自身の環境に書き換える

shell でそのファイルを読み込み，環境変数としてアクセスできるようにする

#### setup on GCP

- アカウント登録
- プロジェクトを作成

#### install `gcloud` and `gsutil` command

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

#### 静的 IP アドレスの確保

GCE_STATIC_IP_ADDRESS

#### ドメインの確保

freenom など

### 1. load RDF data

- `data/` 以下にロード対象の RDF データを置く
- `initialLoader.sql` に必要な処理を書く

- virtuoso コンテナを建てる
- ローカルのフォルダがマウントされ，`.virtuoso` というフォルダが作成される
  - `data/` もマウントされている

```shell
docker-compose up -d  virtuoso
```

起動中のコンテナに対して，ISQL 経由でデータをロードするように指示を出す

```shell
nohup docker exec -i virtuoso_container isql $PORT_VIRTUOSO_ISQL \
  -U dba -P $PASSWORD_VIRTUOSO < ./initialLoader.sql &
```

`nohup $@ &` とすることで，`$@` に相当するコマンドをバックグラウンドかつ独立して実行する
→ ターミナルを閉じても実行される

（時間がかかる処理によく使われる）

## 2. Upload `virtuoso.db` to GCS by `gsutil`

`<bucket_name>` でバケットの名前を指定して，`gsutil mb` コマンドで作成する
この際に，`-p` オプションでプロジェクトと紐付けできる

```shell
gsutil mb -p $GCE_PROJECT_NAME gs://<bucket_name>
gsutil cp .virtuoso/virtuoso.db gs://<bucket_name>
```

## 3. Create instance by `gcloud`

```shell
gcloud compute instances create $GCE_INSTANCE_NAME \
 --project $GCE_PROJECT_NAME \
 --zone $GCE_ZONE \
 --machine-type $GCE_MACHINE_TYPE \
 --tags $GCE_TAGS \
 --create-disk $GCE_CREATE_DISK \
 --metadata-from-file NGINX_CONFIG=$PWD/nginx/default.conf.template,DOTENV=$PWD/.env,COMPOSE_FILE=$PWD/docker-compose.yml,startup-script=$PWD/gcp/startup.sh \
 --metadata google-logging-enabled=true,cos-metrics-enabled=true,USERNAME=$USERNAME \
 --address $GCE_STATIC_IP_ADDRESS \
 --shielded-secure-boot \
 --shielded-vtpm \
 --shielded-integrity-monitoring
```

## 4. complete !

confirm your page

## future work

GitHub Actions との連携：例えば，リポジトリ内の `data/` 以下に変更があったら，それをトリガーに virtuoso コンテナの起動 → データのロード →GCS との同期もできるはず

## LICENSE

[_MIT_](https://github.com/Ningensei848/virtuoso-on-gcp-with-cos/blob/main/LICENSE)
