"""
This Python script helps in the setup of the CloudCV Server code on 
a new machine. Just run this code and relax. 

This code is written for Linux based systems and tested on Ubuntu 14.04

Author - Prashant Jalan
"""

#Module import
from string import Template
import os
import redis

#Check root privilege
if os.geteuid() != 0:
	exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

#Check redis server
rs = redis.Redis("localhost")
if not rs.ping():
	exit("The redis server is not running.\nMake sure you have configured the redis server to run robustly at its default port. Exiting.")

#Stopping nginx server if it is already running
if not os.system('/etc/init.d/nginx status'):
	print "Stopping nginx server."
	os.system('nginx -s stop')

project_path = os.path.dirname(os.path.abspath(__file__))
#Pre-defined values
values = dict()
values['django_address']='127.0.0.1:8000'
values['node_address']='127.0.0.1:5000'
values['node_port']='5000'
values['IP_address']='54.147.160.171'
values['server_port']='80'
values['project_path']=project_path
values['user']='ubuntu'
values['caffe_path']='/home/ubuntu/caffe'
values['virtualenv_path']='/home/ubuntu/cloudcv/ccv'

#Setting up the chat.js file
print "\nSetting up the ./nodejs/chat.js file."
tmp = Template(open(project_path+'/nodejs/chat.js').read())
new = tmp.safe_substitute(values)
print "Overwriting the ./nodejs/chat.js file with system specific values."
out = open(project_path+'/nodejs/chat.js', 'w')
out.write(new)
out.close()
print "Done."

#Setting up the conf.py file
print "\nSetting up the ./app/conf.py file."
tmp = Template(open(project_path+'/app/conf.py').read())
new = tmp.safe_substitute(values)
print "Overwriting the ./app/conf.py file with system specific values."
out = open(project_path+'/app/conf.py', 'w')
out.write(new)
out.close()
print "Done."

#Setting up the cloudcv17_uwsgi.ini file
print "\nSetting up the cloudcv17_uwsgi.ini file."
tmp = Template(open(project_path+'/cloudcv17_uwsgi.ini').read())
new = tmp.safe_substitute(values)
print "Overwriting the cloudcv17_uwsgi.ini file with system specific values."
out = open(project_path+'/cloudcv17_uwsgi.ini', 'w')
out.write(new)
out.close()
print "Done."

#Setting up the fileupload_nginx.conf file
print "\nSetting up the fileupload_nginx.conf file."
tmp = Template(open(project_path+'/fileupload_nginx.conf').read())
new = tmp.safe_substitute(values)
print "Overwriting the fileupload_nginx.conf file with system specific values."
out = open(project_path+'/fileupload_nginx.conf', 'w')
out.write(new)
out.close()
print "Copying the file to the /etc/nginx/sites-enabled/ folder"
if os.path.islink('/etc/nginx/sites-enabled/fileupload_nginx.conf'):
	os.system("rm /etc/nginx/sites-enabled/fileupload_nginx.conf")
os.system("cp "+project_path+"/fileupload_nginx.conf /etc/nginx/sites-enabled/fileupload_nginx.conf")
print "Done."

#Ensuring nginx starts up on system reboot
print "\nEnsuring nginx starts up on system reboot."
os.system('update-rc.d nginx defaults')

#Starting nginx server
print "Starting nginx server."
os.system('nginx')
os.system('/etc/init.d/nginx status')

#Starting the uswgi process
print "\nSetting up the uwsgi process."
if not os.path.isdir('/etc/uwsgi'):
	os.system('mkdir /etc/uwsgi')
print "Copying the cloudcv17_uwsgi.ini to /etc/uwsgi"
os.system('cp '+project_path+'/cloudcv17_uwsgi.ini /etc/uwsgi/')
print "Creating upstart for uWSGI emperor"
script = """
# Emperor uWSGI script

description "uWSGI Emperor"
start on runlevel [2345]
stop on runlevel [06]

respawn

exec uwsgi --emperor /etc/uwsgi
"""
out = open('/etc/init/emperor.uwsgi.conf', 'w')
out.write(script)
out.close()
print "Starting uWSGI emperor."
os.system('start emperor.uwsgi')

#Handling forever node.js
print "\nStopping all forever instances"
os.system('/home/ubuntu/cloudcv/node_modules/forever/bin/forever stopall')
print "Starting forever for ./nodejs/chat.js"
foreverStartCMD = '/home/ubuntu/cloudcv/node_modules/forever/bin/forever start '+project_path+'/nodejs/chat.js'
os.system(foreverStartCMD)

#Creating upstart script for forever
print "\nCreating upstart script for forever"
script = """
# Node.js forever script

description "node.js forever"
start on startup
"""
script += "exec " + foreverStartCMD + "\n"
out = open('/etc/init/forever.nodejs.conf', 'w')
out.write(script)
out.close()

print "\nSetup completed successfully. Your server is up and running.\n"
