# ElasticSearch 2.x Template for Zabbix 3.0
Creator : Samih Gribi

It work in Linux and Windows environment.
You have to adapt the file UserParameter.es_zabbix.conf where your script is located

The template allow you to : 

	Monitor ElasticSearch as a Cluster or Standalone
	Discover and Monitor ElasticSearch Nodes of the Cluster
	Monitor the State of the cluster (Green, Yellow, Red)
	Monitor the availability of the API ElasticSearch (collect data through the api default port 9200)
	Monitor the memory used in percent of the process :
		elasticsearch (Linux) 
		elasticsearch-service-x64 or elasticsearch-service-x86 (Windows)

	Provide Graphs of Nodes and Cluster(s) informations

	Trigger alerts on the ElasticSearch State, API availability and ElasticSearch Process/Service
	
PRE-REQUISITE : 
 
	Windows : 
		Python2.7 installed on the server : https://www.python.org/ftp/python/2.7.13/python-2.7.13.amd64.msi
		Zabbix Sender installed to send data to the proxy/master : C:\Zabbix\zabbix_sender.exe

	Linux : 
		Python2.7 installed on the server : yum install python2.7
		Zabbix Sender installed to send data to the proxy/master : zabbix_sender


	Installing pip :
		curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
		python2.7 get-pip.py

	Install Modules : 

		pip install --upgrade setuptools
		pip install exec_cmd psutil elasticsearch2 re 

	Windows : Create Folder on Windows C:\Temp if not exist
	Linux : Will create logs on /tmp/

	Set the macros : 
		{$ES_HOST} => IP of ElasticSearch Cluster (default 127.0.0.1)
		{$ES_PORT} => Port of ElasticSearch API (default it is 9200)
		{$ES_PROCESS_NAME} => Name of ElasticSearch process name (elasticsearch-service-x64.exe,elasticsearch-service-x86.exe or elasticsearch)
		{$ES_STATUS} => 0 green, 1 yellow, 2 red