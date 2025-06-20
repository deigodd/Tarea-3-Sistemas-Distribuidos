FROM openjdk:8-jdk

ENV HADOOP_VERSION=2.10.2
ENV PIG_VERSION=0.17.0
ENV HADOOP_HOME=/opt/hadoop
ENV PIG_HOME=/opt/pig
ENV JAVA_HOME=/usr/local/openjdk-8
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PIG_HOME/bin:$JAVA_HOME/bin
ENV YARN_APPLICATION_CLASSPATH=$HADOOP_HOME/etc/hadoop,$HADOOP_HOME/share/hadoop/common/*,$HADOOP_HOME/share/hadoop/common/lib/*,$HADOOP_HOME/share/hadoop/hdfs/*,$HADOOP_HOME/share/hadoop/hdfs/lib/*,$HADOOP_HOME/share/hadoop/mapreduce/*,$HADOOP_HOME/share/hadoop/mapreduce/lib/*,$HADOOP_HOME/share/hadoop/yarn/*,$HADOOP_HOME/share/hadoop/yarn/lib/*

# Instalar dependencias
RUN apt-get update && apt-get install -y \
    ssh \
    openssh-server \
    wget \
    vim \
    net-tools \
    sudo \
    procps \
    && apt-get clean

# Configurar SSH
RUN mkdir /var/run/sshd && \
    ssh-keygen -A && \
    sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Hadoop
RUN wget https://downloads.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz && \
    tar -xzf hadoop-${HADOOP_VERSION}.tar.gz -C /opt/ && \
    mv /opt/hadoop-${HADOOP_VERSION} ${HADOOP_HOME} && \
    rm hadoop-${HADOOP_VERSION}.tar.gz

# Pig
RUN wget https://downloads.apache.org/pig/pig-${PIG_VERSION}/pig-${PIG_VERSION}.tar.gz && \
    tar -xzf pig-${PIG_VERSION}.tar.gz -C /opt/ && \
    mv /opt/pig-${PIG_VERSION} ${PIG_HOME} && \
    rm pig-${PIG_VERSION}.tar.gz

ENV PIG_CLASSPATH=${HADOOP_HOME}/etc/hadoop

# Configurar Hadoop
COPY core-site.xml $HADOOP_HOME/etc/hadoop/
COPY hdfs-site.xml $HADOOP_HOME/etc/hadoop/
COPY mapred-site.xml $HADOOP_HOME/etc/hadoop/
COPY yarn-site.xml $HADOOP_HOME/etc/hadoop/

RUN echo "export JAVA_HOME=$JAVA_HOME" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh && \
    echo "export HADOOP_HOME=$HADOOP_HOME" >> ~/.bashrc && \
    echo "export PATH=$PATH" >> ~/.bashrc

RUN useradd -m -s /bin/bash hadoop && \
    echo "hadoop:hadoop" | chpasswd && \
    adduser hadoop sudo && \
    echo 'hadoop ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
    chown -R hadoop:hadoop $HADOOP_HOME

USER hadoop
WORKDIR /home/hadoop

RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 600 ~/.ssh/authorized_keys

COPY --chown=hadoop:hadoop entrypoint.sh /entrypoint.sh
COPY --chown=hadoop:hadoop scripts/ /scripts/

RUN chmod +x /entrypoint.sh

EXPOSE 8088 50070 9000

ENTRYPOINT ["/entrypoint.sh"]