import phe.paillier as paillier, psycopg2,uuid,time,psycopg2.extras,sys,pickle,binascii,datetime, numpy as np

_host="localhost"
_database="gpadmin"
_user="gpadmin"
_password="greenplum"
_s3_endpoint="s3-ap-southeast-2.amazonaws.com"
_s3_bucket="alerting-project"
_s3_finished="_finished_"


def read(file, schema1,i):
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
        time.sleep(10)

    #get table
    time.sleep(1)
    cur = conn.cursor()
    cur.execute("CREATE READABLE EXTERNAL TABLE "+table+" "+schema1+" LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+data_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("SELECT * FROM "+table)
    out = cur.fetchall()
    print(str(datetime.datetime.now()) + " "+str(i) + " : READ ROWS "+id + " / "+ file + " COUNT="+str(len(out)))

    cur.close()
    conn.close()
    return out


def write(upload, file, schema,i):
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
    print(str(datetime.datetime.now()) + " "+str(i) + " : WROTE ROWS "+id + " / "+ file + " COUNT="+str(len(upload)))
    conn.commit()
    cur.close()

def serialise(input):
    return binascii.b2a_base64(pickle.dumps(input)).decode('ascii')

def deserialise(input):
    return pickle.loads(binascii.a2b_base64(input.encode('ascii')))

init = np.linspace(-5, 5, 20)

# We generate a 2D grid
x1, x2 = np.meshgrid(init, init)

# To get reproducable values, provide a seed value
np.random.seed(1)

# Z is the elevation of this 2D grid
y = 3*x1 - 0.5*x2 + np.random.normal(size=x1.shape)

x1 = x1.flatten()
x2 = x2.flatten()
y = y.flatten()

alpha = 0.1
n = float(len(x1))
x1_theta = 0
x2_theta = 0
gradients = [0] * len(x1)

def additionScenario():
    iterations = 100
    party = sys.argv[1]

    #initialise
    if party == "y":
        #process keys
        pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)
        key = serialise(pubkey)
        write([[key]], "pubkey/", "(key float)",-1)
    elif party == "x1":
        pubkey = deserialise((read("pubkey/", "(key float)",-1))[0][0])
    elif party == "x2":
        #process keys
        pubkey = deserialise((read("pubkey/", "(key float)",-1))[0][0])
    for i in range(0, iterations):
        if party == "x1":
            x1_prediction = x1 * x1_theta
            write(x1_prediction,"x1/"+str(i)+"/","(x1_prediction float)",i)
            gradient = read("gradient/"+str(i)+"/","(gradient float)",i)
            x1_theta = x1_theta - (alpha / n) * sum(gradient * x1)
        elif party == "x2":
            x1_prediction = read("x1/"+str(i)+"/","(x1_prediction float)",i)
            x2_prediction = x1_prediction + x2 * x2_theta
            write(x2_prediction,"x2/"+str(i)+"/","(x2_prediction float)",i)
            gradient = read("gradient/"+str(i)+"/","(gradient float)",i)
            x2_theta = x2_theta - (alpha / n) * sum(gradient * x2)
        elif party == "y":
            x2_prediction = read("x2/"+str(i)+"/","(x2_prediction float)",i)
            gradient = x2_prediction - y
            write(gradient,"gradient/"+str(i)+"/","(gradient float)",i)
    print("FINISHED")



additionScenario()