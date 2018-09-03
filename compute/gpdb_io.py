import psycopg2,uuid,time,psycopg2.extras,datetime

status = open("gpdb_io.log", "a",1)
polling = open("gpdb_polling.log", "a",1)

host = ""
database = ""
user = ""
password = ""
s3_endpoint = ""
s3_bucket = ""

def init(in_host, in_database, in_user, in_password, in_s3_endpoint, in_s3_bucket):
    global host, database, user, password, s3_endpoint, s3_bucket
    host = in_host
    database = in_database
    user = in_user
    password = in_password
    s3_bucket = in_s3_bucket
    s3_endpoint = in_s3_endpoint



#preserve ordering of list
def writeOrdered(input):
    return [x + [i] for i,x in list(enumerate(input))]

#preserve ordering of list
def readOrdered(data):
    def getKey(elem):
        return elem[len(elem)-1]
    data.sort(key=getKey)
    return [x[:len(x)-1] for x in data]

def read(file, schema1,i):
    schema1 = "("+schema1 +",row_index int)"
    conn = psycopg2.connect(host=host,database=database, user=user, password=password)

    poll_file = "finished_"+file
    data_file = "data_"+file
    cur = conn.cursor()

    #Create tables
    id = str(uuid.uuid1()).replace("-","_")
    pollTable = "poll_"+id
    table = "s3_"+id

    cur.execute("CREATE READABLE EXTERNAL TABLE "+pollTable+" (value text) LOCATION ('s3://"+s3_endpoint+"/"+s3_bucket+"/"+poll_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.close()
    while True:
        polling.write(str(datetime.datetime.now()) + " "+str(i) + " : POLLING "+pollTable + " / "+ poll_file + "\r\n" )
        cur = conn.cursor()
        cur.execute("SELECT * FROM "+pollTable)
        if cur.rowcount == 1:
            break
        cur.close()
        time.sleep(15)
    polling.write(str(datetime.datetime.now()) + " "+str(i) + " : ##### FINISHED POLLING #### "+pollTable + " / "+ poll_file + "\r\n")

    #get table
    time.sleep(1)
    cur = conn.cursor()
    cur.execute("CREATE READABLE EXTERNAL TABLE "+table+" "+schema1+" LOCATION ('s3://"+s3_endpoint+"/"+s3_bucket+"/"+data_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("SELECT * FROM "+table)
    out = cur.fetchall()
    status.write(str(datetime.datetime.now()) + " "+str(i) + " : READ ROWS "+id + " / "+ file + " COUNT="+str(len(out))+"\r\n")

    cur.close()
    conn.close()
    return readOrdered(out)


def write(data, file, schema,i):
    schema = "("+schema +",row_index int)"
    upload = writeOrdered(data)
    conn = psycopg2.connect(host=host,database=database, user=user, password=password)
    # poll status table
    poll_file = "finished_"+file
    data_file = "data_"+file
    cur = conn.cursor()

    #Create tables
    id = str(uuid.uuid1()).replace("-","_")
    pollTable = "poll_"+id
    table = "s3_"+id
    stagingTable = "staging_"+id

    cur.execute("CREATE WRITABLE EXTERNAL TABLE "+pollTable+" (value text) LOCATION ('s3://"+s3_endpoint+"/"+s3_bucket+"/"+poll_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("CREATE WRITABLE EXTERNAL TABLE "+table+" "+schema+" LOCATION ('s3://"+s3_endpoint+"/"+s3_bucket+"/"+data_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("CREATE TABLE "+stagingTable+" "+schema)
    psycopg2.extras.execute_values(cur, "insert into "+stagingTable+" VALUES %s", upload, template=None, page_size=1000)
    cur.execute("INSERT INTO "+table + " SELECT * FROM " + stagingTable)
    conn.commit()
    cur.execute("DROP TABLE "+stagingTable)
    conn.commit()
    cur.execute("INSERT INTO "+pollTable+" (value) VALUES (%s)","1")
    conn.commit()
    status.write(str(datetime.datetime.now()) + " "+str(i) + " : WROTE ROWS "+id + " / "+ file + " COUNT="+str(len(upload))+"\r\n")
    conn.commit()
    cur.close()