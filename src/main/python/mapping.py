import phe.paillier as paillier, psycopg2,uuid,time

_host="localhost"
_database="gpadmin"
_user="gpadmin"
_password="greenplum"
_s3_endpoint="s3-ap-southeast-2.amazonaws.com"
_s3_bucket="ifs-cloud"
_s3_finished="_finished_"
pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)

def read_table(file, schema):
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
    cur.execute("CREATE READABLE EXTERNAL TABLE "+table+" "+schema+" LOCATION ('s3://"+_s3_endpoint+"/"+_s3_bucket+"/"+file+" config=/home/gpadmin/s3.conf') FORMAT 'csv'")
    cur.execute("SELECT * FROM "+table)
    row = cur.fetchone()
    while row is not None:
        print(row)
        row = cur.fetchone()
    cur.close()
    conn.close()

read_table("mock4.csv","(key text, value text)")




#row = cur.fetchone()
#while row is not None:
#    print(row)
#    row = cur.fetchone()
