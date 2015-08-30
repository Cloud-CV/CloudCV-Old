FROM cloudcv/base:latest

MAINTAINER Prashant Jalan

RUN git clone https://github.com/batra-mlp-lab/CloudCV_Server.git --branch workspaces
RUN chmod 775 -R /CloudCV_Server/cloudcv17/media/* 
RUN cd CloudCV_Server && easy_install `cat requirements.txt`
