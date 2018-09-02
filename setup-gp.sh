#!/bin/bash
exec &>> setup-gp.log
source /usr/local/gpdb/greenplum_path.sh

#
# Trap signals here for graceful shutdown
#
function cleanup {
gpstop -a
#sudo service sshd stop
exit
}

trap cleanup SIGTERM SIGINT SIGHUP


#
# Start SSH first
#
#sudo service sshd start
sudo /usr/bin/ssh-keygen -A
sudo /usr/sbin/sshd &

#
# Initialize instance the first time we start
#
if [ ! -s "$MASTER_DATA_DIRECTORY" ]; then
echo "secret = \""$S3_SECRET"\"" >> /home/gpadmin/s3.conf
echo "accessid = \""$S3_ACCESSID"\"" >> /home/gpadmin/s3.conf
export MASTER_HOSTNAME=$(hostname)

/usr/local/bin/discover_segments.sh
gpssh-exkeys -f /tmp/gpdb-hosts
gpinitsystem -a -c  /tmp/gpinitsystem.conf -h /tmp/gpdb-hosts
psql -d template1 -c "alter user gpadmin password 'greenplum'"
createdb gpadmin
psql -d gpadmin -c "CREATE OR REPLACE FUNCTION write_to_s3() RETURNS integer AS '\$libdir/gps3ext.so', 's3_export' LANGUAGE C STABLE"
psql -d gpadmin -c "CREATE OR REPLACE FUNCTION read_from_s3() RETURNS integer AS '\$libdir/gps3ext.so', 's3_import' LANGUAGE C STABLE"
psql -d gpadmin -c "CREATE PROTOCOL s3 (writefunc = write_to_s3, readfunc = read_from_s3)"
gpstop -a
echo "host all all 0.0.0.0/0 md5" >> $MASTER_DATA_DIRECTORY/pg_hba.conf

fi


#
# Start instance
#
gpstart -a