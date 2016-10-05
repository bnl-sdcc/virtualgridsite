#!/usr/bin/env python

from ConfigParser import SafeConfigParser
import classad


def noroute():
    """

    for jobs that cannot be routed
    """


    ad = classad.ClassAd()
    ad['Name'] = 'No_route'
    ad['TargetUniverse'] = 5
    
    ad['set_noreroute'] = "True"
    ad['set_PeriodicRemove'] = classad.ExprTree( '( JobStatus == 1 && (time() - EnteredCurrentStatus) > 10)' )
    ad['EditJobInPlace'] = True
    
    
    exp = 'TARGET.virtualgridsite_interactive_vm =?= UNDEFINED'
    exp += ' && TARGET.virtualgridsite_image_name =?= UNDEFINED'
    exp += ' && TARGET.noreroute =?= UNDEFINED'
    
    f = SafeConfigParser()
    f.readfp( open("/etc/virtualgridsite/static.conf") )
    for sect in f.sections():
        exp += ' && ( TARGET.opsysname != "%s" || TARGET.opsysmajorversion != "%s" ) ' %(f.get(sect, "opsysname"), f.get(sect, "opsysmajorversion"))
    
    v = SafeConfigParser()
    v.readfp( open("/etc/virtualgridsite/images.conf") )
    for sect in v.sections():
        exp += ' && ( TARGET.opsysname != "%s" || TARGET.opsysmajorversion != "%s" ) ' %(v.get(sect, "opsysname"), v.get(sect, "opsysmajorversion"))
    
    ad['Requirements'] = classad.ExprTree(exp)

    return ad

    
def route():
    """

    for jobs that can be routed
    but no interactive mode
    """


    ad = classad.ClassAd()
    ad['Name'] = 'route'
    ad['TargetUniverse'] = 5

    exp = 'TARGET.virtualgridsite_interactive_vm =?= UNDEFINED'
    exp += ' && ( TARGET.virtualgridsite_image_name =!= UNDEFINED'

    f = SafeConfigParser()
    f.readfp( open("/etc/virtualgridsite/static.conf") )
    for sect in f.sections():
        exp += ' || ( TARGET.opsysname == "%s" && TARGET.opsysmajorversion != "%s" ) ' %(f.get(sect, "opsysname"), f.get(sect, "opsysmajorversion"))

    v = SafeConfigParser()
    v.readfp( open("/etc/virtualgridsite/images.conf") )
    for sect in v.sections():
        exp += ' || ( TARGET.opsysname != "%s" && TARGET.opsysmajorversion != "%s" ) ' %(v.get(sect, "opsysname"), v.get(sect, "opsysmajorversion"))

    exp += ')'


    ad['Requirements'] = classad.ExprTree(exp)

    return ad


def interactive():
    """

    for jobs to boot an interactive VM
    """

  
    ad = classad.ClassAd()
    ad['Name'] = 'interactive'
    ad['TargetUniverse'] = 9
    ad['GridResource'] = 'ec2 url'
    # the real value of the URL will be set at the TRANSLATE hook

    exp = 'TARGET.virtualgridsite_interactive_vm == "true"'
    ad['Requirements'] = classad.ExprTree(exp)

    return ad
    

# =============================================================================


noroutead = noroute()
print noroutead

routead = route()
print routead

# being static, can be hardcoded in the condor-ce config file
#interactivead = interactive()
#print interactivead

    """
    """
    """
    """
    """
    """
