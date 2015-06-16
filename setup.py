"""
This Python script helps in the setup of the CloudCV Server code on 
a new machine. Just run this code and relax. 

This code is written for Linux based systems and tested on Ubuntu 14.04
"""

#Module import
from string import Template
import os

#Check root privilege
if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

#Pre-defined values
values = dict()
values['node_address']='127.0.0.1:5000'
values['IP_address']='54.147.160.171'
values['project_path']='/home/ubuntu/cloudcv/cloudcv_gsoc'
values['user']='ubuntu'
values['caffe_path']='/home/ubuntu/caffe'

#Setting up the conf.py file
print "\nSetting up the ./app/conf.py file."
tmp = Template(open('./app/conf.py').read())
new = tmp.safe_substitute(values)
print "Overwriting the ./app/conf.py file with system specific values."
out = open('./app/conf.py', 'w')
out.write(new)
out.close()
print "Done.\n"

#Setting up the fileupload_nginx.conf file
print "\nSetting up the fileupload_nginx.conf file."
tmp = Template(open('fileupload_nginx.conf').read())
new = tmp.safe_substitute(values)
print "Overwriting the fileupload_nginx.conf file with system specific values."
out = open('fileupload_nginx.conf', 'w')
out.write(new)
out.close()
print "Creating a link to the /etc/nginx/sites-enabled/ folder"
if os.path.islink('/etc/nginx/sites-enabled/fileupload_nginx.conf'):
	os.system("rm /etc/nginx/sites-enabled/fileupload_nginx.conf")
os.system("ln -s ./fileupload_nginx.conf /etc/nginx/sites-enabled/fileupload_nginx.conf")
print "Done.\n"

print "Setup completed successfully. Your server is up and running."
