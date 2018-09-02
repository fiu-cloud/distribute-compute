import phe.paillier as paillier, psycopg2,uuid,time,psycopg2.extras,pickle,binascii,datetime, numpy as np,sys
party = sys.argv[1]
_s3_endpoint = sys.argv[2]
_s3_bucket = sys.argv[3]
_host = sys.argv[4]
_database = sys.argv[5]
_user = sys.argv[6]
_password = sys.argv[7]
_s3_finished = "_finished_"
# experiment parameters
iterations = 10
alpha = 0.1

#setup log
status = open("io_status.log", "a",1)
thetas = open("thetas.txt", "a",1)


def serialisePubKey(inputPubKey):
    return str(inputPubKey.n)

def deserialisePubKey(inputSerialisedKey):
    return paillier.PaillierPublicKey(int(inputSerialisedKey))

def serialiseEncrypted(inputEncrypted):
    return str(inputEncrypted.ciphertext()) + " " +str(inputEncrypted.exponent)

def deserialiseEncrypted(pubKey, input):
    cipher,exponent = input.split(" ")
    output = paillier.EncryptedNumber(pubKey, int(cipher), int(exponent))
    return output

def writeOrdered(input):
    return [x + [i] for i,x in list(enumerate(input))]

def readOrdered(data):
    def getKey(elem):
        return elem[len(elem)-1]
    data.sort(key=getKey)
    return [x[:len(x)-1] for x in data]

def serialisePriKey(input):
    return binascii.b2a_base64(pickle.dumps(input)).decode('ascii')

def deserialisePriKey(input):
    return pickle.loads(binascii.a2b_base64(input.encode('ascii')))

def read(file, schema1,i):
    schema1 = "("+schema1 +",row_index int)"
    conn = psycopg2.connect(host=_host,database=_database, user=_user, password=_password)

    poll_file = "finished_"+file
    data_file = "data_"+file
    cur = conn.cursor()

    #Create tables
    id = str(uuid.uuid1()).replace("-","_")
    pollTable = "poll_"+id
    table = "s3_"+id

    cur.execute("CREATE READABLE EXTERNAL TABLE "+pollTable+" (value text) LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+poll_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.close()
    while True:
        cur = conn.cursor()
        cur.execute("SELECT * FROM "+pollTable)
        if cur.rowcount == 1:
            break
        cur.close()
        time.sleep(1)

    #get table
    time.sleep(1)
    cur = conn.cursor()
    cur.execute("CREATE READABLE EXTERNAL TABLE "+table+" "+schema1+" LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+data_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("SELECT * FROM "+table)
    out = cur.fetchall()
    status.write(str(datetime.datetime.now()) + " "+str(i) + " : READ ROWS "+id + " / "+ file + " COUNT="+str(len(out))+"\r\n")

    cur.close()
    conn.close()
    return readOrdered(out)


def write(data, file, schema,i):
    schema = "("+schema +",row_index int)"
    upload = writeOrdered(data)
    conn = psycopg2.connect(host=_host,database=_database, user=_user, password=_password)
    # poll status table
    poll_file = "finished_"+file
    data_file = "data_"+file
    cur = conn.cursor()

    #Create tables
    id = str(uuid.uuid1()).replace("-","_")
    pollTable = "poll_"+id
    table = "s3_"+id
    stagingTable = "staging_"+id

    cur.execute("CREATE WRITABLE EXTERNAL TABLE "+pollTable+" (value text) LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+poll_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")

    cur.execute("CREATE WRITABLE EXTERNAL TABLE "+table+" "+schema+" LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+data_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("CREATE TABLE "+stagingTable+" "+schema)

    psycopg2.extras.execute_values(cur, "insert into "+stagingTable+" VALUES %s", upload, template=None, page_size=1000)

    cur.execute("INSERT INTO "+table + " SELECT * FROM " + stagingTable)
    conn.commit()
    cur.execute("INSERT INTO "+pollTable+" (value) VALUES (%s)","1")
    conn.commit()
    status.write(str(datetime.datetime.now()) + " "+str(i) + " : WROTE ROWS "+id + " / "+ file + " COUNT="+str(len(upload))+"\r\n")
    conn.commit()
    cur.close()


def main():
    # generate synthetic data & initialise variables
    init = np.linspace(-5, 5, 20)
    x1, x2 = np.meshgrid(init, init)
    np.random.seed(1)
    y = 3*x1 - 0.5*x2 + np.random.normal(size=x1.shape)
    x1 = x1.flatten()
    x2 = x2.flatten()
    y = y.flatten()
    n = float(len(x1))
    x1_theta = 0
    x2_theta = 0

    # initialise
    if party == "y":
        x1 = []
        x2 = []
        pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)
        key = serialisePubKey(pubkey)
        write([[key]], "pubkey/", "key text",-1)
    elif party == "x1":
        y = []
        x2 = []
        pubkey = deserialisePubKey((read("pubkey/", "key text",-1))[0][0])
    elif party == "x2":
        y = []
        x1 = []
        pubkey = deserialisePubKey((read("pubkey/", "key text",-1))[0][0])

    # gradient descent
    for i in range(0, iterations):
        if party == "x1":
            x1_prediction = x1 * x1_theta
            x1_prediction_encrypted = list(map(lambda x: [serialiseEncrypted(pubkey.encrypt(x))], x1_prediction))
            write(x1_prediction_encrypted,"x1/"+str(i)+"/","x1_prediction text",i)
            g1 = read("gradient/"+str(i)+"/","gradient float",i)
            x1_gradient = [a[0]*b for a,b in zip(g1,x1)]
            x1_diff = sum(x1_gradient)
            x1_theta = x1_theta - (alpha / n) * x1_diff
            thetas.write("x1 "+ str(x1_theta) + "["+str(x1_diff)+"]\r\n")
        elif party == "x2":
            x1_prediction_serialised = read("x1/"+str(i)+"/","x1_prediction text",i)
            x1_prediction = list(map(lambda x: deserialiseEncrypted(pubkey,x[0]) , x1_prediction_serialised))
            x2_prediction = x1_prediction + x2 * x2_theta
            x2_prediction_encrypted = list(map(lambda x: [serialiseEncrypted(x)], x2_prediction))
            write(x2_prediction_encrypted,"x2/"+str(i)+"/","x2_prediction text",i)
            g2 = read("gradient/"+str(i)+"/","gradient float",i)
            x2_gradient = [a[0]*b for a,b in zip(g2,x2)]
            x2_diff = sum(x2_gradient)
            x2_theta = x2_theta - (alpha / n) * x2_diff
            thetas.write("x2 "+ str(x2_theta) + "["+str(x2_diff)+"]\r\n")
        elif party == "y":
            x2_predictionSerialised = read("x2/"+str(i)+"/","x2_prediction text",i)
            x2_prediction = list(map(lambda x: prikey.decrypt(deserialiseEncrypted(pubkey,x[0])) , x2_predictionSerialised))
            gradient = x2_prediction - y
            gradientOut = list(map(lambda x: [x] ,gradient))
            write(gradientOut,"gradient/"+str(i)+"/","gradient float",i)



main()
