# Description
This docker image is a self contained example of privacy preserving distributed linear regression (gradient descent). This image can be easily modified for other models.

# Architecture
This is a simple system that executes deterministic privacy-preserving non-concurrent (but distributed) algorithms among 2 or more parties.  It should be easy to understand and convey to partner organisations.

Our term 'distributed' is defined as each party holds different data which they want others to calculate on without exposing the raw data itself.

Uses a central file store (AWS S3) to orchestrate the containers the algorithm and transfer immutable data among parties. A critical programming constaint is:  **Each table (data file of ordered collection of rows) can only be written once by only 1 party**  ```gpdb_io.write(data, file, schema,i)``` (ie. immutable table). There may be multiple consumers of this table/file (ie. 1:M messaging). While a party is doing calculations or uploading data all other parties are blocked on am I/O read poll to S3. 

In the S3 bucket 
* data files are prefixed with the word 'data_'. The last column of each row is an automatically generated row_number (in python we assume an array / list has consistent ordering)
* polling files (for pessimistic blocking) are prefixed with the word 'finished_'. This tells the subscribers that the data file is ready to be consumed. _Each data file requires a corresponding polling file_


A more complex system would be required if there are any of the following are requirements 
 * High throughput (many operations / second) parallel processing among 2+ containers. _This system is designed for batch processing of each operation running for minutes to hours_. If you require high throughput use a high level messaging system such as akka
 * Data doesnt't fit in memory (~ 1M encrypted single column rows requires 10GB or ram. If you need this, re-write this system in Spark or some type of MPP system (eg. GP)


# Scenario
There are 3 parties. y, x1, x2. Party y hosts the labels and party x1 and x2 each host a predictor. 
Using gradient descent we are calculating ```y = 31*x1 - 5.5*x2```.
We generate random synthetic data (with random noise). Please refer to ```test/test_local_linear_regression.py``` to see a simple local example of this. The actual distributed code (using paillier homomorphic encryption) is in ```distributed_linear_regression_3_parties.py```. Edit this file to change experiment parameters (such as: constants, iteration count, number of rows, learning rate). S3 and greenplum configuration should be set when you run the docker image (please see below).  

# Data Flow
The data flow is linear. Each operation reads from an S3 'folder' and writes to **another** S3 folder. Only **1** party can subscribe to an S3 folder which will be produces by another party (ie. 1:1 messaging). If you break this paradigm the system will return unexpected results as its not designed to be concurrent or run non-deterministic algorithms.

In the code ```distributed_linear_regression_3_parties.py``` initially party y generates the private/public key pair and publishes the public key to S3. In each iteration of the gradient descent algorithm each party write/reads to the S3 bucket.

step|iteration|s3 folder |party|operation        |
----|---------|----------|-----|------------------
0   |         |pubkey    |y    |write public key
1   |0        |pubkey    |x1   |read public key      
1   |0        |pubkey    |x2   |read public key
2   |0        |x1/0      |x1   |write x1 predictions
3   |0        |x1/0      |x2   |read x1 predictions 
4   |0        |x2/0      |x2   |write x2 predictions
5   |0        |x2/0      |y    |read x2 predictions
6   |0        |gradient/0|y    |write gradient 
7   |0        |gradient/0|x1   |read gradient
7   |0        |gradient/0|x2   |read gradient 
2   |1        |x1/1      |x1   |write x1 predictions
3   |1        |x1/1      |x2   |read x1 predictions 
4   |1        |x2/1      |x2   |write x2 predictions
5   |1        |x2/1      |y    |read x2 predictions
6   |1        |gradient/1|y    |write gradient 
7   |1        |gradient/1|x1   |read gradient 
7   |1        |gradient/1|x1   |read gradient 
8   |2        |x1/2      |x1   |write x1 predictions
    |etc... |||

Note: On each 'read gradient' operation the party updates its private theta(s) which changes the predictions for the next iteration




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

We assume the S3 endpoint is Sydney in the example ```s3-ap-southeast-2.amazonaws.com```. Scenario ```y = 31*x1 - 5.5*x2```.


Your underlying operating system running the docker containers **must** use amazon ntp servers (sycing time). If you do not set this than you will get S3-RequestTimeTooSkewed error on large file uploads/downloads. This cannot be set in the docker container (as it uses time from the non virtualised operating system)
* Linux users read https://www.allcloud.io/how-to/how-to-fix-amazon-s3-requesttimetooskewed/
* MacOS users go to 'System Preferences -> Date & Time -> Select "Set Date & Time Automatically", type in ```0.amazon.pool.ntp.org, 1.amazon.pool.ntp.org, 2.amazon.pool.ntp.org, 3.amazon.pool.ntp.org``` in selection box and **press enter** than save '. _Alternatively (if you have root access) edit /etc/ntp.conf with the servers from the https://www.allcloud.io/how-to/how-to-fix-amazon-s3-requesttimetooskewed/ and restart ntp_
* Windows users read https://timetoolsltd.com/time-sync/how-to-synchronize-microsoft-windows-to-a-ntp-server/, and set the ntp servers to ```0.amazon.pool.ntp.org, 1.amazon.pool.ntp.org, 2.amazon.pool.ntp.org, 3.amazon.pool.ntp.org```

<br />
For processing 1M rows: At least 80GB disc & 12GB ram / container is recommended. Note: Only 1 container does 'heavy work' at any one time (others are blocked) so can use shared resource on a local deployment. Temporary GP staging tables are automatically removed after IO
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
actual = 5.5
```
docker exec x2_container cat thetas.log
```

### 5. Inspect progress
```
docker exec (y_container) cat gpdb_io.log
```

#Know issues
## PHE (N1 analytics) library.
* After initial encryption the exponents are in plaintext (leaked). Can mitigate by adding a constant encrypted number or adjusting max_exponent. Refer to ```tests/test_exponents.py``` 
* After more than 17 additions (on the same encrypted number) the library breaks. Refer to ```test/test_phe_multiplications.py```
* Key lengths on more than 1024 bits result in exponentially longer compute times. 100ms instead of 1ms. Is 1024 bits ok?
## Algorithm (gradient descent)
* Gradients are unencrypted so if parties x1 and x2 collude (share their data) they can discover the labels from y. To mitigate this encrypt the gradients. 
