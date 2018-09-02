#!/bin/bash
exec &>> gpdb-entrypoint.log
setup-gp.sh
python3.6 program.py \
$PARTY \
$S3_ENDPOINT \
$S3_BUCKET \
$GP_HOST \
$GP_DATABASE \
$GP_USER \
$GP_PASSWORD