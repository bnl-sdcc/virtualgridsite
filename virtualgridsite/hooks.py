#!/usr/bin/env python 

import classad
import datetime
import getpass
import hashlib
import logging
import os
import sys
import time
import urllib
import urllib2

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
        self.nova = self._init_nova()
        self.glance = self._init_glance()
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

    # FIXME
    # too much duplicated code here !!
    def _init_nova(self):
        self.novaconf = SafeConfigParser()
        self.novaconf.readfp(open('/etc/virtualgridsite/nova.conf'))
        VERSION = self.novaconf.get('NOVA', 'VERSION')
        USERNAME = self.novaconf.get('NOVA', 'OS_USERNAME')
        PASSWORD = self.novaconf.get('NOVA', 'OS_PASSWORD')
        TENANT = self.novaconf.get('NOVA', 'OS_TENANT_NAME')
        URL = self.novaconf.get('NOVA', 'OS_AUTH_URL')
        nova = NovaCore(VERSION, USERNAME, PASSWORD, TENANT, URL)
        return nova
    
    def _init_glance(self):
        VERSION = self.novaconf.get('NOVA', 'VERSION')
        USERNAME = self.novaconf.get('NOVA', 'OS_USERNAME')
        PASSWORD = self.novaconf.get('NOVA', 'OS_PASSWORD')
        TENANT = self.novaconf.get('NOVA', 'OS_TENANT_NAME')
        URL = self.novaconf.get('NOVA', 'OS_AUTH_URL')
        glance = GlanceCore(USERNAME, PASSWORD, TENANT, URL)
        return glance


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
            if 'virtualgridsite_interactive_vm' in self.ad:
                self._set_interactive()
            else:
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

        if 'virtualgridsite_interactive_vm' in self.ad:
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
            # 1. check the URL 
            url = self.ad['virtualgridsite_image_url']
            self.log.info('detected classad virtualgridsite_image_url %s' %url)
            url_date = urllib2.urlopen(url).info()['last-modified']
            self.log.info('last modified = %s' %url_date)
            # FIXME: 
            #   what if the HTTP headers do not have field "last-modified"? 
            #   What if the format of the date is different?
            image_name = '%s-%s' %(hashlib.md5(url).hexdigest(), datetime.datetime.strptime(url_date, "%a, %d %b %Y %H:%M:%S %Z").strftime('%s') )
            
            # check if already in glnace
            try:
                check = self.glance.get_image(image_name)
                self.log.info('the image %s is already in glance' %image_name)
            except:
                self.log.info('the image %s is not yet glance' %image_name)
                # download the image
                fimage = '%s/images/%s' %(os.path.expanduser("~"), image_name)
                # FIXME
                #   timeout? 
                #   re-trials? 
                #   what to do if the download fails?
                urllib.urlretrieve(url, fimage) 
                # upload to glance 
                self._create_image(fimage, image_name)
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
            i_ami = imagesconf.get(sect, "ami")
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
                image.ami = i_ami
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
            flavor_classad = classad.ClassAd({"name": flavorsconf.get(sect, "name"), "memory":i_memory,"disksize":i_disk,"xcount":i_corecount})
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


    def _set_interactive(self):
        '''
        add to the job classad the needed attributes
        to allow this job to be re-reouted, properly, as an EC2 one
        '''

        self.ad['EC2AccessKeyId'] = "/etc/virtualgridsite/key"
        self.ad['EC2SecretAccessKey'] = "/etc/virtualgridsite/key.secret"

        self.ad['EC2SecurityGroups'] = "default"
        self.ad['EC2AmiID'] = self.image.ami
        self.ad['EC2InstanceType'] = self.flavor.name

        ip = self.nova.get_next_floating_ip()
        self.log.info("next floating ip is %s" %ip.ip)
        self.ad['EC2ElasticIp'] = str(ip.ip)

        self.ad['JobUniverse'] = 9
        self.ad['GridResource'] = "ec2 %s" %self.novaconf.get("EC2", "EC2_URL")



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
               self.log.info('image %s does not match because opsys' %image.get('name'))
               return False
        if "opsysname" in self.ad:
            if self.ad.get('opsysname') != image.get('opsysname'):
               self.log.info('image %s does not match because opsysname' %image.get('name'))
               return False
        if "opsysmajorversion" in self.ad:
            if self.ad.get('opsysmajorversion') != image.get('opsysmajorversion'):
               self.log.info('image %s does not match because opsysmajorversion' %image.get('name'))
               return False
        if "opsysminorversion" in self.ad:
            if self.ad.get('opsysminorversion') != image.get('opsysminorversion'):
               self.log.info('image %s does not match because opsysminorversion' %image.get('name'))
               return False
        self.log.info('image %s matches' %image.get('name'))
        return True


    def _matches_flavor_requirements(self, flavor):
        """
        check if the OpenStack Flavor matches
        the self.ad requirements
        """

        if "maxMemory" in self.ad:
            if int(self.ad.get('maxMemory')) > int(flavor.get('memory')):
               self.log.info('flavor %s does not match because memory' %flavor.get('name'))
               return False
        if "disk" in self.ad:
            if int(self.ad.get('disksize')) > int(flavor.get('disksize')):
               self.log.info('flavor %s does not match because disksize' %flavor.get('name'))
               return False
        if "xcount" in self.ad:
            if int(self.ad.get('xcount')) > int(flavor.get('xcount')):
               self.log.info('flavor %s does not match because xcout' %flavor.get('name'))
               return False
        self.log.info('flavor %s matches' %flavor.get('name'))
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




