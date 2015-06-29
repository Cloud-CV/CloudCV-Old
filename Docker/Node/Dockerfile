FROM buildpack-deps:jessie

MAINTAINER Prashant Jalan

RUN gpg --keyserver pool.sks-keyservers.net --recv-keys 7937DFD2AB06298B2293C3187D33FF9D0246406D 114F43EE0176B71C7BC219DD50A3051F888C628D

ENV NODE_VERSION 0.12.5
ENV NPM_VERSION 2.11.3

RUN curl -SLO "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.gz" \
	&& curl -SLO "https://nodejs.org/dist/v$NODE_VERSION/SHASUMS256.txt.asc" \
	&& gpg --verify SHASUMS256.txt.asc \
	&& grep " node-v$NODE_VERSION-linux-x64.tar.gz\$" SHASUMS256.txt.asc | sha256sum -c - \
	&& tar -xzf "node-v$NODE_VERSION-linux-x64.tar.gz" -C /usr/local --strip-components=1 \
	&& rm "node-v$NODE_VERSION-linux-x64.tar.gz" SHASUMS256.txt.asc \
	&& npm install -g npm@"$NPM_VERSION" \
	&& npm install socket.io@0.9.17 \
	&& npm install archiver@0.13.1 \
	&& npm install redis@0.12.1 \
	&& npm install sqlite3@3.0.4 \
	&& npm install node-fs@0.1.7 \
	&& npm install cookie@0.1.2 \
	&& npm install forever@0.13.0 \
	&& npm cache clear

COPY chat.js /home/user/chat.js
COPY run.sh /home/user/run.sh
CMD ["bash", "/home/user/run.sh"]
