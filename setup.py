#!/usr/bin/env python
#

import commands
import os
import re
import sys

from distutils.core import setup
from distutils.command.install import install as install_org
from distutils.command.install_data import install_data as install_data_org


from virtualgridsite import core
release_version = core.__version__ 

# ===========================================================
#                D A T A     F I L E S 
# ===========================================================


etc_files = ['etc/nova/nova.conf',
             'etc/virtualgridsite/images.conf',
             'etc/virtualgridsite/flavors.conf',
             'etc/virtualgridsite/virtualgridsite.conf',
            ]
#etc_condor_files = ['etc/condor/99-nova.config',]
etc_condorce_files = ['etc/condor-ce/99-nova.config',]


share = ['share/condor_ce_router_defaults_nova',
         'share/nova_hook_job_cleanup',
         'share/nova_hook_job_exit',
         'share/nova_hook_translate_job',
         'share/nova_hook_update_job_info',
        ]


rpm_data_files=[('/etc/virtualgridsite', etc_files),
                #('/etc/condor/config.d', etc_condor_files),
                ('/etc/condor-ce/config.d', etc_condorce_files),
                ('/usr/share/virtualgridsite', share),
               ]


# -----------------------------------------------------------

def choose_data_files():
    rpminstall = True
    userinstall = False
     
    if 'bdist_rpm' in sys.argv:
        rpminstall = True

    elif 'install' in sys.argv:
        for a in sys.argv:
            if a.lower().startswith('--home'):
                rpminstall = False
                userinstall = True
                
    return rpm_data_files
       
# ===========================================================

# setup for distutils
setup(
    name="virtualgridsite",
    version=release_version,
    description='virtualgridsite package',
    long_description='''This package contains virtualgridsite''',
    license='GPL',
    author='Jose Caballero',
    author_email='jcaballero@bnl.gov',
    maintainer='Jose Caballero',
    maintainer_email='jcaballero@bnl.gov',
    url='https://github.com/jose-caballero/virtualgridsite',
    # we include the test/ subdirectory
    packages=['virtualgridsite',
              ],

    scripts = [ ],
    
    data_files = choose_data_files()
)
