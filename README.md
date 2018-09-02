# Description
This docker image is a self contained example of privacy preserving distributed linear regression (gradient descent). 

# Scenario
There are 3 parties. y, x1, x2. Party y contains the labels and party x1 and x2 each contain a predictor. 
Using gradient descent we are calculating ```y = 3*x1 - 0.5*x2```.
We generate random synthetic data (with random noise). Please refer to ```test/test_local_linear_regression.py``` to see a simple local example of this. The actual distributed code (using paillier homomorphic encryption) is in the folder ```compute```. To change experiment parameters please change them in ```distributed_linear_regression_3_parties.py```. S3 and greenplum configuration should be set when you run the docker image (please see below).  

## Remove scenario (all containers)
```
docker stop y_container
docker rm y_container
docker stop x1_container
docker rm x1_container
docker stop x2_container
docker rm x2_container
echo "all removed"
```

## Run scenario
You can build and run this scenario on your local computer(s) or in the cloud by following the following script.
 
### 1. Download / Build gpdb (greenplum db 5.11) image
 Ensure you have built docker image ```fiucloud/gpdb``` prior to this. 
 
 Source code ```https://gitlab.com/openfiu/gpdb``` or use pre-built docker image can be accessed by running ```docker pull fiucloud/gpdb```

### 2. Build this image
```
docker build . -t fiucloud/compute
```

### 3. Setup S3
Setup an S3 bucket and generate secret and accessid for this.

### 4. Run the 3 containers 

We assume the S3 endpoint is Sydney in the example ```s3-ap-southeast-2.amazonaws.com```. Scenario ```y = 3*x1 - 0.5*x2```.

<br />

##### Party Y (private key holder & labels)
port 5432
```
docker run --name y_container \
-e PARTY='y' \
-e S3_BUCKET='!!!ADD ME!!!' \
-e S3_SECRET='!!!ADD ME!!!' \
-e S3_ACCESSID='!!!ADD ME!!!' \
-e S3_ENDPOINT='s3-ap-southeast-2.amazonaws.com' \
-e GP_HOST='localhost' \
-e GP_DATABASE='gpadmin' \
-e GP_USER='gpadmin' \
-e GP_PASSWORD='greenplum' \
-i -t -p 5432:5432 -d fiucloud/compute
```

<br />

##### Party x1 
port 5431
```
docker run --name x1_container \
-e PARTY='x1' \
-e S3_BUCKET='!!!ADD ME!!!' \
-e S3_SECRET='!!!ADD ME!!!' \
-e S3_ACCESSID='!!!ADD ME!!!' \
-e S3_ENDPOINT='s3-ap-southeast-2.amazonaws.com' \
-e GP_HOST='localhost' \
-e GP_DATABASE='gpadmin' \
-e GP_USER='gpadmin' \
-e GP_PASSWORD='greenplum' \
-i -t -p 5431:5432 -d fiucloud/compute
```


<br />

##### Party x2
port 5430
```
docker run --name x2_container \
-e PARTY='x2' \
-e S3_BUCKET='!!!ADD ME!!!' \
-e S3_SECRET='!!!ADD ME!!!' \
-e S3_ACCESSID='!!!ADD ME!!!' \
-e S3_ENDPOINT='s3-ap-southeast-2.amazonaws.com' \
-e GP_HOST='localhost' \
-e GP_DATABASE='gpadmin' \
-e GP_USER='gpadmin' \
-e GP_PASSWORD='greenplum' \
-i -t -p 5430:5432 -d fiucloud/compute
```

### 4. Inspect Results 

See the party's thetas. This can be run at any time to monitor the progress.
Format of this is
```party theta[change]```<br /><br />
##### Party x1 
actual = 3
```
docker exec x1_container cat thetas.log
```
```
First 3 iterations along the lines of...
x1 3.1135774539365526[-3113.5774539365525]
x1 3.055918612196987[57.65884173956543]
x1 3.056986368525498[-1.0677563285108405]
```

<br />

##### Party x2
actual = -0.5
Note (It's imporbable this theta will converge very well due to the noise. If it were are large value, such as -50 would converge)
```
docker exec x2_container cat thetas.log
```
