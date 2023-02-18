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

# Create folders to save data files with information about token for NDAC-API session and UE ICC IDs 
RUN mkdir -p /opt/nifi/nifi-current/icc-ids
RUN mkdir -p /opt/nifi/nifi-current/tokens

COPY docker/nifi-central/monitor-central.pagoda.local.crt /usr/lib/jvm/java-11-openjdk-amd64/bin/monitor-central.pagoda.local.crt
COPY docker/nifi-central/monitor-central.pagoda.local.key /usr/lib/jvm/java-11-openjdk-amd64/bin/monitor-central.pagoda.local.key

RUN cd /usr/lib/jvm/java-11-openjdk-amd64/bin && \ 
 keytool -import -trustcacerts -keystore cacerts -storepass monitorcentralpagoda -noprompt -alias monitor-central.pagoda.local.crt -file monitor-central.pagoda.local.crt 

