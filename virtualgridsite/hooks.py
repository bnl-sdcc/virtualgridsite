#!/usr/bin/env python 

import classad
import getpass
import logging
import sys
import time

from novissima.novacore import NovaCore
from novissima.glancecore import GlanceCore
from ConfigParser import SafeConfigParser


class Image(object):
    def __init__(self):
        self.name = None
        self.ami = None
        self.opsys = None
        self.opsysname = None
        self.opsysmajorversion = None

class Flavor(object):
    def __init__(self):
        self.name = None
        self.memory = None
        self.xcount = None
        self.disksize = None


class hook_base(object):

    def __init__(self, ad=None):
        self.ad = ad
        self.username = getpass.getuser()
        self._setlogging()
        self.nova = _init_nova()
        self.glance = _init_glance()
        self.conf = SafeConfigParser()
        self.conf.readfp( open('/etc/virtualgridsite/virtualgridsite.conf') )


    def _setlogging(self):

        self.log = logging.getLogger()

        logfilename = '/var/log/virtualgridsite/hooks.%s.log' %self.username
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

        self.log.debug('input class ad:\n%s' %self.ad)

        requires = self._requires_vm()
        self.log.info('_requires_vm() returned %s' %requires)
        if requires:
            self._choose_vm()
            self._boot_os_server()
            self._build_requirements()

        return self.ad


   def _requires_vm(self):
        '''
        decides if booting a VM server in OpenStack is needed or not
        '''
        
        if self.conf.getboolean('VIRTUALGRIDSITE', 'always_vm'):
            return True
        # FIXME
        # this can be done probably with self.ad.get('foo')
        if 'opsys' in self.ad and self.conf.has_option('VIRTUALGRIDSITE','farm_opsys') and self.ad['opsys'] != self.conf.get('VIRTUALGRIDSITE', 'farm_opsys'):
            return True
        if 'opsysname' in self.ad and self.conf.has_option('VIRTUALGRIDSITE','farm_opsysname') and self.ad['opsysname'] != self.conf.get('VIRTUALGRIDSITE', 'farm_opsysname'):
            return True
        if 'opsysmajorversion' in self.ad and self.conf.has_option('VIRTUALGRIDSITE','farm_opsysmajorversion') and self.ad['opsysmajorversion'] != self.conf.get('VIRTUALGRIDSITE', 'farm_opsysmajorversion'):
            return True

        if 'virtualgridsite_image_name' in self.ad:
            return True

        if 'virtualgridsite_url' in self.ad:
            return True

        # if no reason to boot a VM...
        return False


    def _choose_vm(self):

        self.image = self._choose_image()
        if not self.image:
            self.log.critical('no image found. Aborting')
            raise Exception
        else:
            self.log.info('found image name = %s ' %self.image.name)

        self.flavor = self._choose_flavor()
        if not self.flavor:
            self.log.critical('no flavor found. Aborting')
            raise Exception
        else:
            self.log.info('found flavor name = %s' %self.flavor.name)


    def _choose_image(self):

       if 'virtualgridsite_image_url' in self.ad:
            self.log.info('detected classad virtualgridsite_image_url. Uploading image to glance')
            # 1. check the URL and download the image
            # 2. upload to glance
            image_name = 'fake-image-for-test'  # this should be the md5sum of the URL
            # 3. upload to glance
            self._create_image('/home/slot1/image.iso', image_name)
            self.log.info('image uploaded to glance')

            image = Image()
            image.name = image_name
            return image


        if 'virtualgridsite_image_name' in self.ad:
            image_name = self.ad['virtualgridsite_image_name']
            self.log.info('using image name passed as classad: %s' %image_name)
            image = Image()
            image.name = image_name
            return image

        imagesconf = SafeConfigParser()
        imagesconf.readfp(open('/etc/virtualgridsite/images.conf'))
        for sect in imagesconf.sections():
            i_opsys = imagesconf.get(sect,"opsys")
            i_opsysname = imagesconf.get(sect,"opsysname")
            i_opsysmajorversion = imagesconf.get(sect,"opsysmajorversion")
            image_classad = classad.ClassAd({"opsys":i_opsys,"opsysname":i_opsysname,"opsysmajorversion":i_opsysmajorversion})
            self.log.info('image class ad:\n %s' %image_classad.printOld())
            check = self._matches_image_requirements(image_classad)
            if check:
                self.log.info('image %s and job match? %s' %(sect, check))
                image_name = imagesconf.get(sect, "name")
                self.log.info('image found: %s' %image_name)

                image = Image()
                image.name = image_name
                image.opsys = i_opsys
                image.opsysname = i_opsysname
                image.opsysmajorversion = i_opsysmajorversion
                return image
                
        # if nothing found...
        return None


    def _choose_flavor(self):

        if 'virtualgridsite_flavor_name' in self.ad:
            flavor_name = self.ad['virtualgridsite_flavor_name']
            self.log.info('using flavor name passed as classad: %s' %flavor_name)
            flavor = Flavor()
            flavor.name = flavor_name
            return flavor


        flavorsconf = SafeConfigParser()
        flavorsconf.readfp(open('/etc/virtualgridsite/flavors.conf'))
        for sect in flavorsconf.sections():
            i_memory = flavorsconf.get(sect,"memory")
            i_disk = flavorsconf.get(sect,"disksize")
            i_corecount = flavorsconf.get(sect,"xcount")
            flavor_classad = classad.ClassAd({"memory":i_memory,"disksize":i_disk,"xcount":i_corecount})
            self.log.info('flavor class ad:\n %s' %flavor_classad.printOld())
            check = self._matches_flavor_requirements(flavor_classad)
            if check:
                self.log.info('flavor %s and job match? %s' %(sect, check))
                flavor_name = flavorsconf.get(sect, "name")
                self.log.info('flavor found: %s' %flavor_name)
                flavor = Flavor()
                flavor.name = flavor_name
                flavor.memory = i_memory
                flavor.xcount = i_corecount
                flavor.disksize = i_disk
                return flavor


        # if nothing found...
        return None




    # FIXME!
    # for now, the names of image & flavor are hardcoded
    def _boot_os_server(self):

        self.log.info('init boot_os_server')
        server_name = self.ad['GlobalJobId']
        self.log.info('booting VM server with server name = %s, image name = %s, flavor name = %s' %(server_name, self.image.name, self.flavor.name))
        try:
            self.nova.create_server(server_name, self.image.name, self.flavor.name)        
        except Exception, ex:
            self.log.critical('booting VM server failed. Aborting')
            raise Exception
        self.log.info('end boot_os_server')
        self.ad['virtualgridsite_os_servername'] = server_name 


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


    def _create_image(self, filename, image_name):
        '''
        uploads a VM image into glance
        '''
        self.glance.create_image(filename, image_name)



class hook_update(hook_base):
    '''
    code to be invoked by the _HOOK_UPDATE_JOB_INFO hook. 
    ad is the job classad 
    '''
    def __init__(self, ad):
        hook_base.__init__(self, ad)
        self.log = logging.getLogger('update')

    def run(self):

        self.log.debug('input class ad:\n%s' %self.ad)
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
        self.log.debug("begin")
        self.log.debug('input class ad:\n%s' %self.ad)
        if 'virtualgridsite_os_servername' in self.ad:
            servername = self.ad['virtualgridsite_os_servername']
            self.log.info('classad includes virtualgridsite_os_servername %s' %servername)
            self.log.info('deleting OpenStack server %s' %servername)
            server = self.nova.get_server(servername)
            self.nova.delete_server(server)



# =============================================================================

# FIXME
# too much duplicated code here !!
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

def _init_glance():
    c = SafeConfigParser()
    c.readfp(open('/etc/virtualgridsite/nova.conf'))
    VERSION = c.get('NOVA', 'VERSION')
    USERNAME = c.get('NOVA', 'OS_USERNAME')
    PASSWORD = c.get('NOVA', 'OS_PASSWORD')
    TENANT = c.get('NOVA', 'OS_TENANT_NAME')
    URL = c.get('NOVA', 'OS_AUTH_URL')
    glance = GlanceCore(USERNAME, PASSWORD, TENANT, URL)
    return glance



