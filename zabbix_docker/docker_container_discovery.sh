#!/bin/bash

#==========================================================================
# Summary
#==========================================================================
# Check status of a docker-compose project.
# Created by Samih Gribi.
# Date : 12/05/2017
#==========================================================================

usage(){
    echo "Usage: $0 PROJECT_NAME"
    exit 1
}

case "$1" in
	"-discover")
		#############################################
		# Format the JSON for Zabbix discovery rule #
		#############################################
		echo -e '{ \n';
		echo -e '\t "data":[ \n \n';
	;;
	*)
	;;
esac
FIRST=1
#############################################
#                Function to div()              #
#############################################

div ()
{
	if [ $2 -eq 0 ]; then echo division by 0; exit; fi
	local p=12                            # precision
	local c=${c:-0}                       # precision counter
	local d=.                             # decimal separator
	local r=$(($1/$2)); echo -n $r        # result of division
	local m=$(($r*$2))
	[ $c -eq 0 ] && [ $m -ne $1 ] && echo -n $d
	[ $1 -eq $m ] || [ $c -eq $p ] && return
	local e=$(($1-$m))
	let c=c+1
	div $(($e*10)) $2
}
for entry in "$2"/*
do

	#################################################
	#  Check if the ini file of each project exist  #
	#################################################

	if [ -e $entry/docker-compose.ini ]
		then

		##########################################################################################
		#    Export Environnement variable from the ini file to launch docker-compose command    #
		##########################################################################################

		export $( sed 's/#.*$//g' $entry/docker-compose.ini )

		##########################################################################################
		#        Docker-compose ps -q command is used to get containers longid for each project  #
		#                               Get only 12 first character to get short id                                   #
		##########################################################################################

		ID_CONTAINERS=$( /usr/local/bin/docker-compose ps -q )
		##########################################################################################
		#          Initialize variable First to format the JSON zabbix discovery                 #
		##########################################################################################

		#############################################
		#    For each applications whe get datas    #
		#############################################
		for ID in $ID_CONTAINERS; do

			###############################################
			# Get only 12 first character to get short id #
			###############################################

			ID="${ID:0:12}"

			#############################################
			#         Get details from docker API       #
			#############################################

			JSON=$( echo -e "GET /containers/$ID/json HTTP/1.0\r\n" | nc -U /var/run/docker.sock | tail -1 )

			#############################################
			#   Be sure the container is not to ignore  #
			#############################################

			NAME=$( echo $JSON | python -c 'import sys,json;d=json.loads(sys.stdin.read()); print d["Name"]' )
			if [ $MONITORING_IGNORE ]
			then
				echo $NAME | grep -q -e $MONITORING_IGNORE
			fi
			if [ $? -eq 0 ]
			then
				continue
			fi

			NAMECONTAINER=$( echo $NAME | sed 's/\///' )

			#############################################
			#   Parse JSON and return 2 if not running  #
			#############################################

			STATE=$( echo $JSON | python -c 'import sys,json;d=json.loads(sys.stdin.read()); print d["State"]["Status"]' )
			echo $JSON | python -c 'import sys,json;d=json.loads(sys.stdin.read()); d["State"]["Status"] == u"running"'

			#############################################
			#    Parse JSON to get the Thinpool device  #
			#############################################

			DEVICE=$( echo $JSON | jq -r .GraphDriver.Data.DeviceName )
			VALUES=$( sudo dmsetup status $DEVICE )
			SIZE=$( echo $VALUES | cut -d' ' -f2 )
			USED=$( echo $VALUES | cut -d' ' -f4 )
			USED=$(( $USED*100))
			USED_PERCENT=$(div $USED $SIZE)

			STATS=$( docker stats $NAMECONTAINER --no-stream | tail -1 )
			CPUUSED=$( echo $STATS | awk '{print $2}')
			MEMORYUSED=$( echo $STATS | awk '{print $8}' )

			case "$1" in
				"-sender")
				#############################################
				# Sending datas to Zabbix via zabbix_sender #
				#############################################

				data0="- dockercomposeproject.longid[$ID] $ID_CONTAINERS"
				data1="- dockercomposeproject.name[$ID] $NAMECONTAINER"
				data2="- dockercomposeproject.diskspacepercent[$ID] $USED_PERCENT"
				data3="- dockercomposeproject.state[$ID] $STATE"
				data4="- dockercomposeproject.cpustats[$ID] $CPUUSED"
				data5="- dockercomposeproject.memstats[$ID] $MEMORYUSED"
				data="${data0} \n ${data1}\n ${data2}\n ${data3}\n ${data4}\n ${data5}"
	
				out=`echo -e $data | zabbix_sender -v -c /etc/zabbix/zabbix_agentd.conf -i -`

				#############################################
				#  Verify number of data sent to zabbix (6) #
				#############################################

				if [[ $out == *"processed: 6"* ]]
				then
					echo 0
				else
					echo 1
				fi
			;;
			"-discover")
				#############################################
				# Format the JSON for Zabbix discovery rule #
				#############################################

				if [[ $FIRST == 0 ]];
				then
					echo -e '\t,\n';
				fi
				FIRST=0

				echo -e '\t { \n';
				echo -e '\t \t "{#DOCKER_ID}":"'$ID'" \n';
				echo -e '\t}\n';
			;;
			*)
			;;
			esac
		done
	fi
done

case "$1" in
        "-discover")
			#############################################
			# Format the JSON for Zabbix discovery rule #
			#############################################
			echo -e ' \n \t ] \n';
			echo -e '} \n';
        ;;
        *)
        ;;
esac

