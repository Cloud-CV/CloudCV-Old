CloudCV
=======

# Note: This repository is deprecated now. We will soon start working on the revamped version of CloudCV website very soon.

[![Join the chat at https://gitter.im/batra-mlp-lab/CloudCV](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/batra-mlp-lab/CloudCV?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/Cloud-CV/CloudCV.svg?branch=master)](https://travis-ci.org/Cloud-CV/CloudCV)
[![Requirements Status](https://requires.io/github/Cloud-CV/CloudCV/requirements.svg?branch=master)](https://requires.io/github/Cloud-CV/CloudCV/requirements/?branch=master)


Large-Scale Distributed Computer Vision As A Cloud Service
-----------------------------------------------------------

We are witnessing a proliferation of massive visual data. Unfortunately scaling existing computer vision algorithms to large datasets leaves researchers repeatedly solving the same algorithmic and infrastructural problems. 

Our goal is to democratize computer vision; one should not have to be a computer vision, deep learning, and distributed computing expert to have access to state-of-the-art distributed computer vision algorithms. We provide access to state-of-art distributed computer vision algorithms as a cloud service through Web Interface & APIs. Researchers, Students and Developers will be able to access these distributed computer vision algorithms and the computation power through small number of click and minimal lines of code. 

Instructions to get started with CloudCV development
-----------------------------------------------------

To setup project cloudcv on your local machine, you need install [docker](https://docs.docker.com/mac/) first. After installing docker on your machine, just follow the instructions given in the next section. 

Steps for setting the development environment
---------------------------------------------

1. Run the following git clone (specify a directory of your choosing if you like):

        git clone https://github.com/batra-mlp-lab/CloudCV.git cloudcv

2. Run virtualenv on the git cloned directory to setup the Python virtual environment:

        virtualenv cloudcv

3. cd into the name of the directory into which you cloned the git repository

        cd cloudcv

4. Activate the virtual environment(it is recommended to use virtual environment):

        source bin/activate

5. Change directory to Docker and run the bash script to create Docker containers:

        cd Docker && ./build.sh

6. Change directory to Docker and run the bash script to create Docker containers:

        ./run_server.sh run 80 443
  When the image building completes then you can visit [127.0.0.1](http://127.0.0.1) and check if CloudCV server is running or not. 

7. Now, for setting up workers, just run the command:

        ./worker-cpu

8. Now, visit [http://127.0.0.1](http://127.0.0.1) in your browser and you should be all set.

Additional Information
-----------------------

  * Whenever you want to stop the docker containers, then run the command `./stopContainer`

  * To remove all the images, run the command `docker rm $(docker ps -a -q)`

  * To make yourself familiar with the codebase, check the file [DirectoryDocumentation.txt](https://github.com/batra-mlp-lab/CloudCV/blob/master/DirectoryDocumentation.txt)

  * For any other queries, open issues or you can chat with developers at our [gitter]() channel.

  * Official Documentation available at [this link](http://batra-mlp-lab.github.io/CloudCV/).
