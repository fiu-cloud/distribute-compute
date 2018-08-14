import phe.paillier as paillier, psycopg2,uuid,time,numpy as np

_host="localhost"
_database="gpadmin"
_user="gpadmin"
_password="greenplum"
_s3_endpoint="s3-ap-southeast-2.amazonaws.com"
_s3_bucket="ifs-cloud"
_s3_finished="_finished_"
pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)

#read
#schema is numphy schema
#returns numphy table
def read(file, schema1, schema2):
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
    table = cur.fetchall()
    table = table[1:]
    out = np.array(table,dtype=schema2)
    cur.close()
    conn.close()
    return out


def write(upload, file, schema1, schema2):
    conn = psycopg2.connect(host=_host,database=_database, user=_user, password=_password)
    # poll status table
    poll_file = "_finished_"+file
    cur = conn.cursor()

    #Create tables
    pollTable = "tbl"+str(uuid.uuid1()).replace("-","_")
    cur.execute("CREATE WRITABLE EXTERNAL TABLE "+pollTable+" (value text) LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+poll_file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    table = "tbl"+str(uuid.uuid1()).replace("-","_")
    cur.execute("CREATE WRITABLE EXTERNAL TABLE "+table+" "+schema1+" LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")

    #upload data
    for row in upload:
        cur.execute("INSERT INTO "+table+" "+schema2,row)
    cur.execute("INSERT INTO "+pollTable+" (value) VALUES (%s)","1")
    cur.close()



table = read("mock2.csv","(key text, value text)",[('key', 'U10'), ('value', 'U10')])
write(table,"mock3.csv","(key text, value text)","(key, value) VALUES (%s, %s)")

