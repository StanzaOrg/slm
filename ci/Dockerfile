FROM ubuntu:18.04
RUN apt-get update -y
RUN apt-get install -y python3 git wget unzip gcc

ENV STANZA_VERSION=0_14_33
RUN wget "http://lbstanza.org/resources/stanza/lstanza_${STANZA_VERSION}.zip" -O stanza.zip
RUN unzip stanza.zip -d /stanza
RUN echo "install-dir = \"/stanza\"" >> ${HOME}/.stanza
RUN echo "platform = linux" >> ${HOME}/.stanza
ENV PATH="/stanza:$PATH"

ENTRYPOINT ci/build.sh
