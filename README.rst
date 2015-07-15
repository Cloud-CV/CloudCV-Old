CloudCV-Server 
=======================

CloudCV is Large Scale Distributed Computer Vision as a Cloud Service.

=======================

A simple introduction to the code:

.
|-- app                                 The main folder for Django 
|   |-- admin.py                        The Django admin.py file used to visualise database, etc
|   |-- celery                          Deprecated. The previous celery worker code.
|   |-- classify_views.py               The views file for classify. cloudcv.org/classify
|   |-- conf.py                         Configuration file. Contains various directory name. Used by many files.
|   |-- core                            Folder containing code used to parse and execute job API calls.
|   |-- decaf_views.py                  The views file for decaf features. cloudcv.org/decaf-server/
|   |-- executable                      Deprecated. Folder container various executables used by previous celery.
|   |-- __init__.py                     It's just needed so that you can import like app.core.executable
|   |-- job.py                          Not sure. Perhaps deprecated.
|   |-- log.py                          Used sometime to log to file, stdout or redis.
|   |-- models.py                       The models file of Django.
|   |-- poi_views.py                    The views file for finding POI. cloudcv.org/vip/
|   |-- response.py                     Not sure. Perhaps deprecated.
|   |-- run_executable.py               Not sure. Perhaps deprecated.
|   |-- savefile.py                     Not sure. Perhaps deprecated.
|   |-- serialize.py                    Not sure. Perhaps deprecated.
|   |-- static                          Static files, of course.
|   |-- templates                       Templates for rendering the html files
|   |-- templatetags                    Used by templates, perhaps.
|   |-- tests.py                        A file written for unit testing. Not complete.
|   |-- thirdparty                      Some thirdparty apps for dropbox, google drive, etc.
|   |-- trainaclass_views.py            The views file for training a class. cloudcv.org/trainaclass/
|   |-- urls.py                         The file specifying the URL mapping
|   |-- utility.py                      Not sure. Perhaps deprecated.
|   |-- views.py                        The views file for image stitching. cloudcv.org/image-stitch/
|   `-- vqa_views.py                    The views file for VQA. It is not public yet.
|-- celeryTasks                         The folder containing all the celery jobs.
|   |-- apiTasks                        The folder containing the celery API jobs.
|   |   |-- caffe_classify.py           Required by tasks.py
|   |   |-- decaf_cal_feature.py        Required by tasks.py
|   |   |-- __init__.py                 Default requirement to call python files in this folder.
|   |   `-- tasks.py                    The main file for API jobs.
|   |-- celery.py                       The main celery file used to initialise the workers.
|   |-- __init__.py                     Default requirement to call python files in this folder.
|   `-- webTasks                        The folder containing all the celery web tasks.
|       |-- classifyTask.py             The classify task. cloudcv.org/classify
|       |-- decafTask.py                Finding decaf features task. cloudcv.org/decaf-server/
|       |-- __init__.py                 Default requirement to call python files in this folder
|       |-- poi_files                   Files required by poiTask.py
|       |-- poiTask.py                  Finding the person of importance task. cloudcv.org/vip/
|       |-- stitch_full                 Image stitch executable. Used by stitchTask.py
|       |-- stitchTask.py               Image stitching task. cloudcv.org/image-stitch/
|       |-- trainTask.py                Train a class task. cloudcv.org/trainaclass/
|       `-- WNID.mat                    File required for finding labels in classifyTask.py
|-- cloudcv17                           Django project folder.
|   |-- __init__.py                     Default requirement to call python files in this folder.
|   |-- logs                            Was used once upon a time to write logs.
|   |-- media                           Folder to store all the media. New files are also downloaded into this.
|   |   `-- pictures                    Folder storing some demo images.
|   |       |-- demo                    Demo images for classify. cloudcv.org/classify
|   |       |-- demo1                   Demo images for image stitch. cloudcv.org/image-stitch/
|   |       |-- poiDemo                 Demo images for person of interest. cloudcv.org/vip/
|   |       `-- vqaDemo                 Demo images for vqa.
|   |-- settings.py                     Settings file for Django app.
|   |-- urls.py                         Default file for Django app.
|   `-- wsgi.py                         Default file for Django app.
|-- cloudcv17_uwsgi.ini                 The uwsgi configurations used to run the Django app.
|-- Docker                              Folder containing all the Dockerfiles and scripts to start server & worker
|   |-- Base                            Base folder
|   |   `-- Dockerfile                  Builds cloudcv/base image
|   |-- Code                            Code folder
|   |   `-- Dockerfile                  Builds the data container cloudcv/code image from cloudcv/base and github.
|   |-- CPUWorker                       Worker folder
|   |   `-- Dockerfile                  Builds the cloudcv/worker-cpu image with graphlab, opencv and caffe.
|   |-- Django                          Django folder
|   |   |-- Dockerfile                  Builds cloudcv/django image from cloudcv/base
|   |   `-- run.sh                      Script to run the django code.
|   |-- Nginx                           Nginx folder
|   |   `-- Dockerfile                  Builds cloudcv/nginx image
|   |-- Node                            Node folder
|   |   |-- Dockerfile                  Builds cloudcv/node image
|   |   `-- run.sh                      Script to run the node code
|   |-- server.sh                       Script to start the server.
|   |-- stopContainer.sh                Script to stop the running containers.
|   `-- worker-cpu.sh                   Script to run the cloudcv worker.
|-- docs                                Sphinx documentation
|-- fileupload_nginx.conf               The config file for nginx. Used by cloudcv/nginx Dockerfile.
|-- manage.py                           The Django manage.py
|-- nodejs                              The node.js application folder
|   `-- chat.js                         The code for Node js. Used by cloudcv/node Dockerfile.
|-- README.rst                          The README
|-- requirements.txt                    The requirements for the Django app. Used by cloudcv/base Dockerfile.
|-- setup.py                            Deprecated. Used before to start the server.
`-- uwsgi_params                        The uswgi params. Used by nginx when running Django.
