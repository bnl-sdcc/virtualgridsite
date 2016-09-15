#!/usr/bin/python

# fake example on how to 
# generate the routing table
# with a script listed in 
#   JOB_ROUTER_ENTRIES_CMD

import classad
import htcondor


anAd = classad.ClassAd()
anAd['Name'] = 'Local_Condor_From_Script'
anAd['TargetUniverse'] = 5
anAd['Requirements'] = classad.ExprTree( '(TARGET.RouteToEC2 =?= UNDEFINED)' )

print anAd

