# AKTE LAHIR KIRANA
FROM ubuntu
MAINTAINER erwan@palawamaya.com

# Persiapan
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y wget git vim sudo nmap python2.7 python-pip default-jre

# User untuk keperluan non container
RUN useradd -ms /bin/bash soekir
RUN mkdir /home/soekir/.kirana 
COPY . /home/soekir/.kirana/
RUN su - soekir -c "cp /home/soekir/.kirana/pocket/bashrc /home/soekir/.bashrc"

# Nmap
RUN wget https://raw.githubusercontent.com/vulnersCom/nmap-vulners/master/vulners.nse -O /usr/share/nmap/scripts/vulners.nse
RUN nmap --script-updatedb

# SSLyze
RUN pip install sslyze

# Owasp ZAP
RUN wget https://github.com/zaproxy/zaproxy/releases/download/v2.8.1/ZAP_2.8.1_Linux.tar.gz -P /root/
RUN tar xzvf /root/ZAP_2.8.1_Linux.tar.gz -C /opt/
RUN rm -rf /root/ZAP_2.8.1_Linux.tar.gz
RUN mv /opt/ZAP_2.8.1 /zap
RUN pip install --upgrade zapcli
