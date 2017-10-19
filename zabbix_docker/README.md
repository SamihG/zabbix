# Docker Template for Zabbix 3.0
Creator : Samih Gribi
Template to monitor Docker (only on Linux) engine, container and compose.

You have to adapt the file UserParameter.docker_zabbix.conf where your script is located

The template allow you to : 

	Discover all Containers located in the macro {$DOCKER_SOURCES}
		Monitor Docker Containers :
			CPU used
			Memory used
			Diskspace used
			Status
		
	Trigger alerts on the Container status (not running) and diskspace of the Container
	
Pre-requisite : 


	User zabbix have to be in docker group
	User zabbix needs sudo rights on /usr/sbin/dmsetup
	Each container has to have ini file named docker-compose.ini
	Zabbix Sender installed to send data to the proxy/master : zabbix_sender
	
	Set the macros : 
		{$DOCKER_LIMIT_DISKPACE} => threshold of disk used space (default it is 80)
		{$DOCKER_SOURCES} => This is the location of docker sources (default it is /home/docker_sources/)
		