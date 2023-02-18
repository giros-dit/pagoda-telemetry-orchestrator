FROM apache/nifi:latest

USER root

RUN apt-get --allow-releaseinfo-change update

# Install Python3
RUN apt-get install -y python3 python3-pip

# Install pytz library using pip
RUN pip install pytz

# Install OpenJDK-11
RUN apt-get update && \
 apt-get install -y openjdk-11-jdk && \
 apt-get install -y ant && \
 apt-get clean;

# Fix certificate issues
RUN apt-get update && \
 apt-get install ca-certificates-java && \
 apt-get clean && \
 update-ca-certificates -f;

# Setup JAVA_HOME -- useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64/
RUN export JAVA_HOME

COPY docker/nifi-mec1/monitor-mec1.pagoda.local.crt /usr/lib/jvm/java-11-openjdk-amd64/bin/monitor-mec1.pagoda.local.crt
COPY docker/nifi-mec1/monitor-mec1.pagoda.local.key /usr/lib/jvm/java-11-openjdk-amd64/bin/monitor-mec1.pagoda.local.key

RUN cd /usr/lib/jvm/java-11-openjdk-amd64/bin && \ 
 keytool -import -trustcacerts -keystore cacerts -storepass monitormec1pagoda -noprompt -alias monitor-mec1.pagoda.local.crt -file monitor-mec1.pagoda.local.crt 

