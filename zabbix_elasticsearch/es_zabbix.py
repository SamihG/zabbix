#!/usr/bin/python2.7

# Created by Samih Gribi on 07 August 2017
# Get ES (windows) Cluster information, nodes & caches informations and Services informations

# Import librairies for json format, elasticsearch and process
import json
import re
import sys
import os
import psutil
import socket
from elasticsearch import Elasticsearch
from exec_cmd import exec_cmd



global directory
if os.name == 'nt' :
        directory = 'C:\TEMP\\'
elif os.name == 'posix' :
        directory = '/tmp/'

if not os.path.exists(directory):
        os.makedirs(directory)



class ZabbixSender:
    """Wrapper class around zabbix_sender command"""

    def __init__(self):
                if os.name == 'nt' :
                        self.zabbix_cfg = 'C:\Zabbix\zabbix_agentd.conf'
                elif os.name == 'posix' :
                        self.zabbix_cfg = '/etc/zabbix/zabbix_agentd.conf'

    def exec_sender(self, infile):
        if os.name == 'nt' :
                cmd = ['C:\Zabbix\zabbix_sender.exe', '-i', infile, '-c', self.zabbix_cfg]
        elif os.name == 'posix' :
                #cmd = ['zabbix_sender', '-i', infile, '-c', self.zabbix_cfg]
                cmd = "zabbix_sender -i %s -c %s" % (infile, self.zabbix_cfg)

        cmd_result = exec_cmd(cmd)
        return cmd_result

    # Known bugs:
    # - Redirected stdout of zabbix_sender
    #   [https://support.zabbix.com/browse/ZBX-6285]
    def _handle_zabbix_sender_out(self, output):
        for line in output.splitlines():
            if line.startswith('info from server'):
                line_spl = line.split(' ')
                try:
                    fail_count = line_spl[line_spl.index('Failed') + 1]
                    if fail_count != '0':
                        # Zabbix sender ran ok but
                        # there is at least 1 failed item
                        return 2
                except ValueError:
                    pass
        # All fine
        return 0

nodename = socket.gethostname()

# Define the fail message
def zbx_fail():
    print "ZBX_NOT_SUPPORTED"
    sys.exit(2)

if len(sys.argv) < 5:
    zbx_fail()


# Initialize elastichsearch connection
# sys.argv[1] is the IP or dns of the elasticsearch cluster
# sys.argv[1] is the Port of elastisearch API (default 9200)
host = sys.argv[1]+':'+sys.argv[2]

try:
        es = Elasticsearch(host,sniff_on_start=False)
except Exception, e:
        zbx_fail()

# Write into a temporary file values for sender
def cluster():
        services_log= open(directory + 'sender_service.log', 'w')

        #Check cluster service available
        if es.ping():
                availability = 0
        else:
                availability = 1
                sys.exit(1)

        #Check service running elasticsearch-service-x86.exe or elasticsearch-service-x64.exe or elasticsearch
        state = 1

        for p in psutil.process_iter():
                if os.name == 'nt' :
                        if p.name() in ['elasticsearch-service-x86.exe','elasticsearch-service-x64.exe']:
                                state = 0
                                memory = p.memory_percent()
                elif os.name == 'posix' :
                        if p.name() in ['java']:
                                regex = re.compile(r'/elasticsearch')
                                if filter(regex.search,p.cmdline()) :
                                        state = 0
                                        memory = p.memory_percent()

        print memory
        services_log.write('- ES[es_memory] ' + `round(memory,2)` + '\n')
        services_log.write('- ES[es_availability] ' + `availability` + '\n')
        services_log.write('- ES[service_state] ' + `state` + '\n')
        services_log.close()

        cluster_log = open(directory + 'sender_cluster.log', 'w')
        #health = json.dumps(es.cluster.health())
        health = es.cluster.health()
        #datahealth = json.loads(health)

        #Tables with all fileds we want to collect
        healthtable = ['status', 'timed_out', 'number_of_nodes', 'number_of_data_nodes', 'active_primary_shards', 'active_shards',
                'relocating_shards', 'initializing_shards', 'unassigned_shards','number_of_pending_tasks', 'number_of_in_flight_fetch',
                'task_max_waiting_in_queue_millis', 'active_shards_percent_as_number', 'delayed_unassigned_shards'
                ]

        returnvals = {}
        for datahealth in es.cluster.health().keys():
                returnvals[datahealth] = health[datahealth]

        for index, (key, value) in enumerate(returnvals.items()):
                if value == 'green':
                        value = 0
                elif value == 'yellow':
                        value = 1
                elif value == 'red':
                        value = 2
                if value == False:
                        value = 0
                elif value == True:
                        value = 1
                if key == 'cluster_name':
                        value = value.replace("'","")
                        value = value.encode("utf-8")
                cluster_log.write('- ES['+key+'] ' + `value` + '\n')
        cluster_log.close()

        if sys.argv[4] == 'sender':
                sender = ZabbixSender()
                sender.exec_sender(infile=directory + 'sender_cluster.log')

                sender = ZabbixSender()
                sender.exec_sender(infile=directory + 'sender_service.log')


        sys.exit(0)

# Return JSON with values related to each nodes : nodename, store size, store throttle time, docs count, docs deleted
def nodes():
        nodes_log= open(directory + 'sender_nodes.log', 'w')

        json_response = {'data': []}
        returnvals = {}
        nodes = es.nodes.stats()

        #Tables with all fileds we want to collect
        indexing = ['delete_time_in_millis', 'noop_update_total', 'index_total', 'index_current', 'delete_total', 'index_time_in_millis', 'delete_current']
        stores = ['size_in_bytes', 'throttle_time_in_millis']
        docs = ['count', 'deleted']
        gets = ['missing_total', 'exists_total', 'current', 'time_in_millis', 'missing_time_in_millis', 'exists_time_in_millis', 'total']
        for node in nodes['nodes'].keys():
                nodenames = es.nodes.stats()['nodes'][node]['name']
                returnvals['{#NODENAME}'] = nodenames

                for store in es.nodes.stats()['nodes'][node]['indices']['store'].keys():
                        #returnvals['{#'+ store + '}'] = es.nodes.stats()['nodes'][node]['indices']['store'][store]
                        if store in stores:
                                nodes_log.write('- ES['+nodenames+'.store.'+store+'] ' + `es.nodes.stats()['nodes'][node]['indices']['store'][store]` + '\n')

                for doc in es.nodes.stats()['nodes'][node]['indices']['docs'].keys():
                        if doc in docs:
                        #returnvals['{#'+ docs + '}'] = es.nodes.stats()['nodes'][node]['indices']['docs'][docs]
                                nodes_log.write('- ES['+nodenames+'.doc.'+doc+'] ' + `es.nodes.stats()['nodes'][node]['indices']['docs'][doc]` + '\n')

                for index in es.nodes.stats()['nodes'][node]['indices']['indexing'].keys():
                        if index in indexing:
                        #returnvals['{#'+ indexing + '}'] = es.nodes.stats()['nodes'][node]['indices']['indexing'][indexing]
                                nodes_log.write('- ES['+nodenames+'.index.'+index+'] ' + `es.nodes.stats()['nodes'][node]['indices']['indexing'][index]` + '\n')

                for get in es.nodes.stats()['nodes'][node]['indices']['get'].keys():
                        if get in gets:
                        #returnvals['{#'+ get + '}'] = es.nodes.stats()['nodes'][node]['indices']['get'][get]
                                nodes_log.write('- ES['+nodenames+'.get.'+get+'] ' + `es.nodes.stats()['nodes'][node]['indices']['get'][get]` + '\n')


                for index, (key, value) in enumerate(returnvals.items()):
                        #print key, value
                        json_response['data'].append({key: value})

        if sys.argv[4] == 'discover':
                print json.dumps(json_response, indent=4)

        nodes_log.close()

        if sys.argv[4] == 'sender':
                sender = ZabbixSender()
                sender.exec_sender(infile=directory + 'sender_nodes.log')

def main():
        if sys.argv[3] == 'cluster':
                cluster()
        elif sys.argv[3] == 'nodes':
                nodes()

main()
