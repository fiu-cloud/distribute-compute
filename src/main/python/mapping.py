import phe.paillier as paillier, psycopg2,uuid,time,psycopg2.extras,sys,pickle,binascii,datetime

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
        time.sleep(1)

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

def additionScenario():
    iterations = 10
    schema = "(a text, b text)"
    rowCount = 1000000
    party = sys.argv[1]
    print(">> "+ party)

    if party == "a":
        #process keys
        pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)
        key = serialise(pubkey)
        write([[key]], "pubkey/", "(key text)",-1)

        #write the initial data
        in_tbl = []
        for i in range(0, rowCount, 1):
            in_tbl.append([str(i),serialise(pubkey.encrypt(i))])
        write(in_tbl,"a/0/",schema,-1)
    elif party == "b":
        #process keys
        pubkey = deserialise((read("pubkey/", "(key text)",-1))[0][0])
    for i in range(0, iterations):
        if party == "a":
            temp = read("b/"+str(i)+"/",schema,i)
            out = list(map(lambda x: [x[0], serialise(deserialise(x[1])+pubkey.encrypt(1))], temp))
            # print(str(i) + " : " + str(temp) + " -> " + str(out))
            write(out,"a/"+str(i+1)+"/",schema,i)
        elif party == "b":
            temp = read("a/"+str(i)+"/",schema,i)
            out = list(map(lambda x: [x[0], serialise(deserialise(x[1])+pubkey.encrypt(1))], temp))
            # print(str(i) + " : " + str(temp) + " -> " + str(out))
            write(out,"b/"+str(i)+"/",schema,i)
    print("FINISHED")

    if party == "a":
        outA = read("a/"+str(iterations)+"/",schema,-1)
        print("A "+str(len(outA)))
        totalA = 0
        for i in outA:
            value = prikey.decrypt(deserialise(i[1]))
            totalA += value
        #    print("A " + str(i[0]) + " -> "+ str(value))
        print("A total " + str(totalA))

        outB = read("b/"+str(iterations - 1)+"/",schema,-1)
        print("A "+str(len(outB)))
        totalB = 0
        for i in outB:
            value = prikey.decrypt(deserialise(i[1]))
            totalB += value
        #    print("B " + str(i[0]) + " -> "+ str(value))
        print("B total " + str(totalB))


additionScenario()