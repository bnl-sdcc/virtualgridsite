#!/usr/bin/env python 

import time
import sys
import classad

from novissima.novacore import NovaCore
from ConfigParser import SafeConfigParser


ss hook_translate(object):
    '''
    
    code to be invoked by the _HOOK_TRANSLATE_JOB hook.
    ad is the job classad 
    '''
    
    def __init__(self, ad):

        self.ad = ad


    def run(self):

        nova = _init_nova()

        imagesconf = SafeConfigParser()
        imagesconf.readfp(open('/etc/virtualgridsite/images.conf'))
        for image in imagesconf.sections():
            i_opsys = imagesconf.get(image,"opsys")
            i_opsysname = imagesconf.get(image,"opsysname")
            i_opsysmajorversion = imagesconf.get(image,"opsysmajorversion")
            image_classad = classad.ClassAd({"opsys":i_opsys,"opsysname":i_opsysname,"opsysmajorversion":i_opsysmajorversion})
            check = _matches_image_requirements(self.ad, image_classad)

        flavorsconf = SafeConfigParser()
        flavorsconf.readfp(open('/etc/virtualgridsite/flavors.conf'))
        for flavor in flavorsconf.sections():
            i_memory = flavorsconf.get(flavor,"memory")
            i_disk = flavorsconf.get(flavor,"disksize")
            i_corecount = flavorsconf.get(flavor,"xcount")
            flavor_classad = classad.ClassAd({"memory":i_memory,"disksize":i_disk,"xcount":i_corecount})
            check = _matches_flavor_requirements(self.ad, flavor_classad)

        return self.ad


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
