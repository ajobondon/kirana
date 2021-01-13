# AKTE LAHIR KIRANA
FROM ubuntu
MAINTAINER erwan@palawamaya.com

# Persiapan
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y wget git vim sudo nmap python3 python3-pip default-jre bc traceroute tcptraceroute dnsutils curl

# User untuk keperluan non container
RUN useradd -ms /bin/bash soekir
RUN mkdir /home/soekir/.kirana 
COPY . /home/soekir/.kirana/
RUN su - soekir -c "cp /home/soekir/.kirana/pocket/bashrc /home/soekir/.bashrc"
RUN chmod 440 /home/soekir/.kirana/pocket/sudoers
RUN chown root.root /home/soekir/.kirana/pocket/sudoers
RUN cp /home/soekir/.kirana/pocket/sudoers /etc/sudoers

# Nmap
RUN wget https://raw.githubusercontent.com/vulnersCom/nmap-vulners/master/vulners.nse -O /usr/share/nmap/scripts/vulners.nse
RUN nmap --script-updatedb

# SSLyze
RUN pip3 install sslyze

# Owasp ZAP
RUN wget https://github.com/zaproxy/zaproxy/releases/download/v2.8.1/ZAP_2.8.1_Linux.tar.gz -P /root/
RUN tar xzvf /root/ZAP_2.8.1_Linux.tar.gz -C /opt/
RUN rm -rf /root/ZAP_2.8.1_Linux.tar.gz
RUN mv /opt/ZAP_2.8.1 /zap
RUN pip3 install --upgrade zapcli

# Arachni
RUN wget https://github.com/Arachni/arachni/releases/download/v1.5.1/arachni-1.5.1-0.5.12-linux-x86_64.tar.gz -P /root/
RUN tar xzvf /root/arachni-1.5.1-0.5.12-linux-x86_64.tar.gz -C /opt/
RUN mv /opt/arachni-1.5.1-0.5.12 /opt/arachni

# TCPing
RUN wget http://www.vdberg.org/~richard/tcpping -O /usr/local/bin/tcping
RUN chmod +x /usr/local/bin/tcping
