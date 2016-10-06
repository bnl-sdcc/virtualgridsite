#!/usr/bin/env python 

import commands
import classad
import htcondor
import os
import time


# FIXME
# this should NOT be hardcoded
# this is just a prototype
COLLECTOR_HOST = 'grid20.racf.bnl.gov'
PORT = '29619'


def submit():

    x509 = os.environ['X509_USER_PROXY']
    
    ad = classad.ClassAd()
    
    ad['JobUniverse'] = 9
    ad['GridResource'] = "condor %s %s:%s" %(COLLECTOR_HOST, COLLECTOR_HOST, PORT)
    ad['ShouldTransferFiles'] = "YES"
    
    f = open('/tmp/job.sh', 'w')
    print >> f, "#!/bin/bash"
    print >> f, "hostname"

    ad['Cmd'] = "/tmp/job.sh"
    ad['Arguments'] = ""
    ad['StreamOut'] = "false"
    ad['StreamErr'] = "false"
    ad['WhenToTransferOutput'] = "ON_EXIT"
    
    ad['virtualgridsite_interactive_vm'] = classad.ExprTree('true')
    ad['virtualgridsite_image_name'] = "centos7-bare-cloud"
    
    ad['x509userproxy'] = x509
    ad['x509userproxysubject'] = commands.getoutput('voms-proxy-info -identity -file %s' %x509)
    ad['x509UserProxyFQAN'] = ','.join( commands.getoutput('voms-proxy-info -fqan -file %s' %x509).split('\n') )
    ad['x509userproxysubject'] = commands.getoutput('voms-proxy-info -vo -file %s' %x509)
    ad['x509UserProxyExpiration'] = int(time.time()) + int( commands.getoutput('voms-proxy-info -timeleft -file %s' %x509) )
    print ad
    
    sc = htcondor.Schedd() 
    clusterid = str(sc.submit(ad, 1))
    return clusterid


def getIP(clusterid):

    coll = htcondor.Collector("%s:%s" %(COLLECTOR_HOST, PORT))
    remote_s = coll.locate(htcondor.DaemonTypes.Schedd, COLLECTOR_HOST)
    remote_sc = htcondor.Schedd(remote_s)
    EC2ElasticIp = None
    while not EC2ElasticIp:
        q = remote_sc.query("true", ['EC2ElasticIp', 'Owner', 'SubmitterGlobalJobId'])
        for i in q:
            if 'SubmitterGlobalJobId' in i and 'EC2ElasticIp' in i:
                if i['SubmitterGlobalJobId'].split('#')[1].split('.')[0] == clusterid:
                    EC2ElasticIp = i['EC2ElasticIp']
        time.sleep(1)
    return EC2ElasticIp



clusterid = submit()
print "new job cluster id = %s" %clusterid

EC2ElasticIp = getIP(clusterid)
print "EC2ElasticIp = %s" %EC2ElasticIp
