FROM ubuntu:18.04
RUN apt-get update -y
RUN apt-get install -y python3 git wget unzip gcc

ENV STANZA_VERSION=0_14_33
RUN wget "http://lbstanza.org/resources/stanza/lstanza_${STANZA_VERSION}.zip" -O stanza.zip
RUN unzip stanza.zip -d /stanza
RUN echo "install-dir = \"/stanza\"" >> /stanza/.stanza
RUN echo "platform = linux" >> /stanza/.stanza
ENV PATH="/stanza:$PATH"
ENV STANZA_CONFIG="/stanza"

ENTRYPOINT ci/build.sh
