#!/usr/bin/env python 

import time
import sys
import classad

from novissima.novacore import NovaCore
from ConfigParser import SafeConfigParser


def translate(ad):
    '''
    code to be invoked by the _HOOK_TRANSLATE_JOB hook.
    ad is the job classad 
    '''
    
    # QUICK & DIRTY TESTS #
    filename = '/tmp/translate.%s' %int(time.time())
    f = open(filename, 'w')
    print >> f, "translate"
    print >> f, '-----'
    # QUICK & DIRTY TESTS #

    nova = _init_nova()

    imagesconf = SafeConfigParser()
    imagesconf.readfp(open('/etc/virtualgridsite/images.conf'))
    for image in imagesconf.sections():
        i_opsys = imagesconf.get(image,"opsys")
        i_opsysname = imagesconf.get(image,"opsysname")
        i_opsysmajorversion = imagesconf.get(image,"opsysmajorversion")
        image_classad = classad.ClassAd({"opsys":i_opsys,"opsysname":i_opsysname,"opsysmajorversion":i_opsysmajorversion})
        print >> f, 'image class ads:'
        print >> f, image_classad.printOld()
        check = _matches_image_requirements(ad, image_classad)
        print >> f, "image %s and job matches? %s" %(image, check)
    
    flavorsconf = SafeConfigParser()
    flavorsconf.readfp(open('/etc/virtualgridsite/flavors.conf'))
    for flavor in flavorsconf.sections():
        f_memory = flavorsconf.get(flavor,"memory")
        f_disk = flavorsconf.get(flavor,"disksize")
        f_corecount = flavorsconf.get(flavor,"xcount")
        flavor_classad = classad.ClassAd({"memory":f_memory,"disksize":f_disk,"xcount":f_corecount})
        print >> f, 'flavor class ads:'
        print >> f, flavor_classad.printOld()
        check = _matches_flavor_requirements(ad, flavor_classad)
        print >> f, "flavor %s and job matches? %s" %(flavor, check)

    return ad




def update(ad):
    '''
    code to be invoked by the _HOOK_UPDATE_JOB_INFO hook. 
    ad is the job classad 
    '''
    return None

    
def exit(ad=None):
    '''
    code to be invoked by the _HOOK_JOB_EXIT hook.
    ad is the job classad 
    '''
    return None


def cleanup(ad):
    '''
    code to be invoked by the _HOOK_JOB_CLEANUP hook. 
    ad is the job classad 
    '''
    pass


# =============================================================================

def _init_nova():
    c = SafeConfigParser()
    c.readfp(open('/etc/virtualgridsite/nova.conf'))
    VERSION = c.get('NOVA', 'VERSION')
    USERNAME = c.get('NOVA', 'OS_USERNAME')
    PASSWORD = c.get('NOVA', 'OS_PASSWORD')
    TENANT = c.get('NOVA', 'OS_TENANT_NAME')
    URL = c.get('NOVA', 'OS_AUTH_URL')
    nova = NovaCore(VERSION, USERNAME, PASSWORD, TENANT, URL)
    return nova


def _matches_image_requirements(job, image):
    """
    check if the OpenStack Image matches
    the job requirements
    """

    if "opsys" in job:
        if job.get('opsys') != image.get('opsys'):
           return False
    if "opsysname" in job:
        if job.get('opsysname') != image.get('opsysname'):
           return False
    if "opsysmajorversion" in job:
        if job.get('opsysmajorversion') != image.get('opsysmajorversion'):
           return False
    if "opsysminorversion" in job:
        if job.get('opsysminorversion') != image.get('opsysminorversion'):
           return False
    return True


def _matches_flavor_requirements(job, flavor):
    """
    check if the OpenStack Flavor matches
    the job requirements
    """

    if "maxMemory" in job:
        if int(job.get('maxMemory')) > int(flavor.get('memory')):
           return False
    if "disk" in job:
        if int(job.get('disksize')) > int(flavor.get('disksize')):
           return False
    if "xcount" in job:
        if int(job.get('xcount')) > int(flavor.get('xcount')):
           return False
    return True
