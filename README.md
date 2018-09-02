```
docker stop y_container
docker rm y_container
docker stop x1_container
docker rm x1_container
docker stop x2_container
docker rm x2_container
docker build . -t fiucloud/compute

docker run --name y_container \
-e PARTY='y' \
-e S3_SECRET='***FILL ME IN***' \
-e S3_ACCESSID='***FILL ME IN***' \
-e S3_ENDPOINT='s3-ap-southeast-2.amazonaws.com' \
-e S3_BUCKET='alerting-project/a' \
-e GP_HOST='localhost' \
-e GP_DATABASE='gpadmin' \
-e GP_USER='gpadmin' \
-e GP_PASSWORD='greenplum' \
-i -t -p 5432:5432 -d fiucloud/compute

docker run --name x1_container \
-e PARTY='x1' \
-e S3_SECRET='***FILL ME IN***' \
-e S3_ACCESSID='***FILL ME IN***' \
-e S3_ENDPOINT='s3-ap-southeast-2.amazonaws.com' \
-e S3_BUCKET='alerting-project/a' \
-e GP_HOST='localhost' \
-e GP_DATABASE='gpadmin' \
-e GP_USER='gpadmin' \
-e GP_PASSWORD='greenplum' \
-i -t -p 5435:5432 -d fiucloud/compute

docker run --name x2_container \
-e PARTY='x2' \
-e S3_SECRET='***FILL ME IN***' \
-e S3_ACCESSID='***FILL ME IN***' \
-e S3_ENDPOINT='s3-ap-southeast-2.amazonaws.com' \
-e S3_BUCKET='alerting-project/a' \
-e GP_HOST='localhost' \
-e GP_DATABASE='gpadmin' \
-e GP_USER='gpadmin' \
-e GP_PASSWORD='greenplum' \
-i -t -p 5434:5432 -d fiucloud/compute

echo("finished")
```
lsof -PiTCP -sTCP:LISTEN

```
docker stop compute
docker rm compute
docker build . -t fiucloud/compute

```

```
docker exec -i -t compute /bin/bash
python3.6 program.py y s3-ap-southeast-2.amazonaws.com alerting-project/a localhost gpadmin gpadmin greenplum

```