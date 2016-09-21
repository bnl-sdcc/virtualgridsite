#!/usr/bin/env python

# =============================================================================
#     code to generate, dynamically,
#     a new route for those jobs that 
#     CANNOT be routed
#     because there is no host and no available
#     VM to run them
# =============================================================================


from ConfigParser import SafeConfigParser
import classad

routead = classad.ClassAd()

routead['Name'] = 'No_route'
routead['TargetUniverse'] = 5

# to prevent the routed job to be re-rerouted
routead['set_noreroute'] = "True"
# to kill the routed job as soon as possible, as it will never run
routead['set_PeriodicRemove'] = classad.ExprTree( '( JobStatus == 1 && (time() - EnteredCurrentStatus) > 10)' )
# to make the routed job to be the same as the source job
routead['EditJobInPlace'] = True

# --------------------------------------------------------------------------
#   building the requirements expression for this Route
# --------------------------------------------------------------------------

exp = 'TARGET.virtualgridsite_interactive_vm =?= UNDEFINED'
exp += ' && TARGET.virtualgridsite_image_name =?= UNDEFINED'

# to prevent the routed job from being re-routed
exp += ' && TARGET.noreroute =?= UNDEFINED'

# no host in the FARM can run the job
f = SafeConfigParser()
f.readfp( open("/etc/virtualgridsite/static.conf") )
for sect in f.sections():
    exp += ' && ( TARGET.opsysname != "%s" || TARGET.opsysmajorversion != "%s" ) ' %(f.get(sect, "opsysname"), f.get(sect, "opsysmajorversion"))

# no VM image currently available in OpenStack can run the job
v = SafeConfigParser()
v.readfp( open("/etc/virtualgridsite/images.conf") )
for sect in v.sections():
    exp += ' && ( TARGET.opsysname != "%s" || TARGET.opsysmajorversion != "%s" ) ' %(v.get(sect, "opsysname"), v.get(sect, "opsysmajorversion"))

routead['Requirements'] = classad.ExprTree(exp)

# --------------------------------------------------------------------------

print routead

