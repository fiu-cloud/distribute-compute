FROM fiucloud/gpdb:latest
USER root
RUN yum install -y \
    https://centos7.iuscommunity.org/ius-release.rpm \
    python36-devel \
    gcc \
    gmp-devel \
    mpfr-devel \
    libmpc-devel

RUN yum install -y python36u-pip
RUN python3.6 -m pip install --upgrade pip
RUN python3.6 -m pip install \
    gmpy2==2.0.8 \
    click==6.7 \
    pycrypto==2.6.1 \
    numpy==1.14.5 \
    nose==1.3.7 \
    psycopg2-binary

#Install phe
RUN git clone https://github.com/n1analytics/python-paillier.git
WORKDIR python-paillier
RUN git fetch --all --tags --prune
RUN git checkout tags/1.4.0
RUN cp -r phe /usr/local/lib/python3.6/site-packages

COPY gpdb-entrypoint.sh /usr/local/bin/gpdb-entrypoint.sh
RUN chmod 755 /usr/local/bin/gpdb-entrypoint.sh

COPY setup-gp.sh /usr/local/bin/setup-gp.sh
RUN chmod 755 /usr/local/bin/setup-gp.sh

COPY src/main/python/lr_gradient_descent.py /home/gpadmin/program.py
RUN chmod 755 /home/gpadmin/program.py

COPY s3.conf /home/gpadmin/s3.conf
RUN chmod 777 /home/gpadmin/s3.conf
RUN echo "" >> /home/gpadmin/s3.conf


USER gpadmin
ENV LOGNAME gpadmin
WORKDIR /home/gpadmin
ENV MASTER_DATA_DIRECTORY=/gpdata/master/gpseg-1
