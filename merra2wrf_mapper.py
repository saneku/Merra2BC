
spec=[
'num_a01 -> 2.59e-17*OC1+3.59e17*OC2+3.11e18*SOA+8.51e17*CB1+2.51e17*CB2+3.65e16*SO4+3.04e16*NH4NO3+6.86e15*NH4;1.0',
'num_a02->1.20e17*OC1+1.20e17*OC2+1.44e18*SOA+1.47e17*CB1+1.47e17*CB2+6.70e16*SO4+5.59e16*NH4NO3+1.26e16*NH4+3.62e17*SA1+7.13e17*[DUST1];1',
'num_a08->6.22e08*OC1+6.22e08*OC2+7.46e09*SOA+2.65e04*CB1+2.65e04*CB2+4.12e10*SO4+3.43e10*NH4NO3+7.74e09*NH4+2.40e13*[DUST4];1',
'OC2 -> .4143*OC2;1.e9',
'DUST_1 -> 1.1738*[DUST1];1.e9',
'DUST_2 -> .939*[DUST2];1.e9',
'DUST_3 -> .2348*[DUST2]+.939*[DUST3];1.e9',
'DUST_5 -> .5869*[DUST4];1.e9',
'SEAS_1 -> 2.*SA1;1.e9',
]

import re

merra_to_wrf_cpec_map={}            #merra to wrf spec map
wrf_mult_map={}                     #wrf multiplier map

def initialise():

    for a in spec:
        m=re.split('->|;',a)
        #print m
        ar=re.findall(r'(-?\ *\.?[0-9]+\.?[0-9]*(?:[Ee]\ *-?\ *[0-9]+)?)\*\[?(\w+)\]?', m[1])
        #m=re.findall(r'(\w+) (\-\>)((-?\ *\.?[0-9]+\.?[0-9]*(?:[Ee]\ *-?\ *[0-9]+)?)\*\[?(\w+)\]?', a[0])
        #http://stackoverflow.com/questions/18152597/extract-scientific-number-from-string
        m[0]=m[0].strip()
        m[2]=float(m[2])
        for r in ar:
            mylist=merra_to_wrf_cpec_map.get(r[1])
            if mylist==None:
                mylist=[]

            mylist.append([m[0],float(r[0])])
            merra_to_wrf_cpec_map.update({r[1]:mylist})
        wrf_mult_map.update({m[0]:m[2]})

    print "\nConversion MAP:"
    for i in merra_to_wrf_cpec_map:
        print i+":\t"+str(merra_to_wrf_cpec_map.get(i))


    print "\nWRF multiplier: MAP"
    for i in wrf_mult_map:
        print i+":\t"+str(wrf_mult_map.get(i))
    print "\n"



initialise()
