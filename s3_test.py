import psycopg2
conn = psycopg2.connect(host="localhost",database="gpadmin", user="gpadmin", password="greenplum")
cur = conn.cursor()
cur.execute("CREATE READABLE EXTERNAL TABLE MOCK (key text, value text) LOCATION ('s3://s3-ap-southeast-2.amazonaws.com/ifs-cloud/mock.csv config=/home/gpadmin/s3.conf') FORMAT 'csv'")
cur.execute("SELECT * FROM MOCK")
print("The number of parts: ", cur.rowcount)
row = cur.fetchone()
while row is not None:
    print(row)
    row = cur.fetchone()
cur.execute("CREATE WRITABLE EXTERNAL TABLE MOCK2 (LIKE MOCK) LOCATION('s3://s3-ap-southeast-2.amazonaws.com/ifs-cloud/mock2.csv config=/home/gpadmin/s3.conf') FORMAT 'csv'")
cur.execute("INSERT INTO MOCK2 SELECT * FROM MOCK")
cur.close()

#CREATE WRITABLE EXTERNAL TABLE ABC (value float8) LOCATION('s3://s3-ap-southeast-2.amazonaws.com/ifs-cloud/tmp config=/home/gpadmin/s3.conf') FORMAT 'csv'
#INSERT INTO ABC SELECT random() as value FROM generate_series(1,1000)