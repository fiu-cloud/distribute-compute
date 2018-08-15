import phe.paillier as paillier, psycopg2,uuid,time,psycopg2.extras

_host="localhost"
_database="gpadmin"
_user="gpadmin"
_password="greenplum"
_s3_endpoint="s3-ap-southeast-2.amazonaws.com"
_s3_bucket="ifs-cloud"
_s3_finished="_finished_"
pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)

def read(file, schema1):
    conn = psycopg2.connect(host=_host,database=_database, user=_user, password=_password)
    # poll status table
    table = "tbl"+str(uuid.uuid1()).replace("-","_")
    poll_file = "_finished_"+file
    cur = conn.cursor()
    cur.execute("CREATE READABLE EXTERNAL TABLE "+table+" (value text) LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+poll_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.close()
    while True:
        cur = conn.cursor()
        cur.execute("SELECT * FROM "+table)
        if cur.rowcount == 1:
            break
        cur.close()
        time.sleep(1)

    #get table
    table = "tbl"+str(uuid.uuid1()).replace("-","_")
    cur = conn.cursor()
    cur.execute("CREATE READABLE EXTERNAL TABLE "+table+" "+schema1+" LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("SELECT * FROM "+table)
    out = cur.fetchall()

    cur.close()
    conn.close()
    return out
# arr = np.matrix([[1, 2, 3 , "a"], [5,6,7,"bc"]])

def write(upload, file, schema):
    conn = psycopg2.connect(host=_host,database=_database, user=_user, password=_password)
    # poll status table
    poll_file = "_finished_"+file
    cur = conn.cursor()

    #Create tables
    id = str(uuid.uuid1()).replace("-","_")
    print("USING "+id)
    pollTable = "poll_"+id
    table = "s3_"+id
    stagingTable = "staging_"+id

    cur.execute("CREATE WRITABLE EXTERNAL TABLE "+pollTable+" (value text) LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+poll_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("CREATE WRITABLE EXTERNAL TABLE "+table+" "+schema+" LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("CREATE TABLE "+stagingTable+" "+schema)

    psycopg2.extras.execute_values(cur, "insert into "+stagingTable+" VALUES %s", upload, template=None, page_size=1000)
    cur.execute("INSERT INTO "+pollTable+" (value) VALUES (%s)","1")
    cur.execute("INSERT INTO "+table + " SELECT * FROM " + stagingTable)

    conn.commit() #do we need this
    cur.close()

def scenario(size):
    schema = "(a text, b integer, c float8)"
    in_tbl = []
    for i in range(0, size, 1):
        in_tbl.append([str(i),i,i+0.5])
    write(in_tbl,"A",schema)
    out = read("A",schema)
    write(out,"B",schema)
    out1 = read("B",schema)
    print(len(out1))
scenario(1000000)

