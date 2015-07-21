python /CloudCV_Server/manage.py migrate
uwsgi --emperor /CloudCV_Server/ --py-autoreload 1
