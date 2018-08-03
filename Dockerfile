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
    nose==1.3.7

#Install phe
RUN git clone https://github.com/n1analytics/python-paillier.git
WORKDIR python-paillier
RUN git fetch --all --tags --prune
RUN git checkout tags/1.4.0
RUN cp -r phe /usr/local/lib/python3.6/site-packages

USER gpadmin
ENV LOGNAME gpadmin
WORKDIR /home/gpadmin
ENV MASTER_DATA_DIRECTORY=/gpdata/master/gpseg-1



#docker build . -t fiucloud/compute
#docker stop compute
#docker rm compute
#docker run --name compute -i -t -p 5432:5432 -d fiucloud/compute
#docker exec -i -t compute /bin/bash