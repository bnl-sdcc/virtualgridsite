#!/usr/bin/env python 

import classad
import getpass
import logging
import sys
import time

from novissima.novacore import NovaCore
from ConfigParser import SafeConfigParser

class hook_base(object):

    def __init__(self, ad=None):
        self.ad = ad
        self._setlogging()

    def _setlogging(self):

        self.log = logging.getLogger()

        username = getpass.getuser()
        logfilename = '/var/log/virtualgridsite/hooks.%s.log' %username
        logStream = logging.FileHandler(logfilename)
        FORMAT='%(asctime)s (UTC) [ %(levelname)s ] %(name)s %(filename)s:%(lineno)d %(funcName)s(): %(message)s'
        formatter = logging.Formatter(FORMAT)
        formatter.converter = time.gmtime  # to convert timestamps to UTC
        logStream.setFormatter(formatter)
        self.log.addHandler(logStream)
        self.log.setLevel(logging.DEBUG)


class hook_translate(hook_base):
    '''
    code to be invoked by the _HOOK_TRANSLATE_JOB hook.
    ad is the job classad 
    '''
    def __init__(self, ad):
        hook_base.__init__(self, ad)
        self.log = logging.getLogger('translate')

    def run(self):

        self.log.info('input class ad:\n%s' %self.ad)

        nova = _init_nova()

        self._choose_vm()

        self._build_requirements()

        return self.ad


    def _choose_vm(self):

        imagesconf = SafeConfigParser()
        imagesconf.readfp(open('/etc/virtualgridsite/images.conf'))
        for image in imagesconf.sections():
            i_opsys = imagesconf.get(image,"opsys")
            i_opsysname = imagesconf.get(image,"opsysname")
            i_opsysmajorversion = imagesconf.get(image,"opsysmajorversion")
            image_classad = classad.ClassAd({"opsys":i_opsys,"opsysname":i_opsysname,"opsysmajorversion":i_opsysmajorversion})
            self.log.info('image class ad:\n %s' %image_classad.printOld())
            check = self._matches_image_requirements(image_classad)
            self.log.info('image %s and job match? %s' %(image, check))

        flavorsconf = SafeConfigParser()
        flavorsconf.readfp(open('/etc/virtualgridsite/flavors.conf'))
        for flavor in flavorsconf.sections():
            i_memory = flavorsconf.get(flavor,"memory")
            i_disk = flavorsconf.get(flavor,"disksize")
            i_corecount = flavorsconf.get(flavor,"xcount")
            flavor_classad = classad.ClassAd({"memory":i_memory,"disksize":i_disk,"xcount":i_corecount})
            self.log.info('flavor class ad:\n %s' %flavor_classad.printOld())
            check = self._matches_flavor_requirements(flavor_classad)
            self.log.info('flavor %s and job match? %s' %(flavor, check))


    def _build_requirements(self):
        """
        builds the classad Requirements based on original job classads
        """
        self.log.info('building Requirements expression')

        reqs = []
        if 'opsys' in self.ad:
            reqs.append( '( Target.OpSys == "%s")' %self.ad.get('opsys'))
        if 'opsysname' in self.ad:
            reqs.append( '( Target.OpSysName == "%s")' %self.ad.get('opsysname'))
        if 'opsysmajorversion' in self.ad:
            reqs.append( '( Target.OpSysMajorVer == %s)' %self.ad.get('opsysmajorversion'))

        if reqs:
            req = classad.ExprTree(' && '.join(reqs))
            self.ad['Requirements'] = req
            self.log.info('Requirements expression built as %s' %req)
        else:
            self.log.info('no Requirements expression built')
            


    def _matches_image_requirements(self, image):
        """
        check if the OpenStack Image matches
        the job requirements
        """

        if "opsys" in self.ad:
            if self.ad.get('opsys') != image.get('opsys'):
               return False
        if "opsysname" in self.ad:
            if self.ad.get('opsysname') != image.get('opsysname'):
               return False
        if "opsysmajorversion" in self.ad:
            if self.ad.get('opsysmajorversion') != image.get('opsysmajorversion'):
               return False
        if "opsysminorversion" in self.ad:
            if self.ad.get('opsysminorversion') != image.get('opsysminorversion'):
               return False
        return True


    def _matches_flavor_requirements(self, flavor):
        """
        check if the OpenStack Flavor matches
        the self.ad requirements
        """

        if "maxMemory" in self.ad:
            if int(self.ad.get('maxMemory')) > int(flavor.get('memory')):
               return False
        if "disk" in self.ad:
            if int(self.ad.get('disksize')) > int(flavor.get('disksize')):
               return False
        if "xcount" in self.ad:
            if int(self.ad.get('xcount')) > int(flavor.get('xcount')):
               return False
        return True


class hook_update(hook_base):
    '''
    code to be invoked by the _HOOK_UPDATE_JOB_INFO hook. 
    ad is the job classad 
    '''
    def __init__(self, ad):
        hook_base.__init__(self, ad)
        self.log = logging.getLogger('update')

    def run(self):

        self.log.info('input class ad:\n%s' %self.ad)
        return None


class hook_exit(hook_base):
    '''
    code to be invoked by the _HOOK_JOB_EXIT hook.
    ad is the job classad 
    '''
    def __init__(self, ad=None):
        hook_base.__init__(self, ad)
        self.log = logging.getLogger('exit')

    def run(self):
        self.log.debug("begin")
        return None


class hook_cleanup(hook_base):
    '''
    code to be invoked by the _HOOK_JOB_CLEANUP hook. 
    ad is the job classad 
    '''
    def __init__(self, ad):
        hook_base.__init__(self, ad)
        self.log = logging.getLogger('cleanup')

    def run(self):
        self.log.info('input class ad:\n%s' %self.ad)


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




