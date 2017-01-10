
import re
import config

#mapping between MERRA2 species and WRF species
chem_map={}                         #merra to wrf spec map
coefficients={}                     #wrf multiplier map

def initialise():

    for a in pathes.spc_map:
        m=re.split('->|;',a)
        #print m
        ar=re.findall(r'(-?\ *\.?[0-9]+\.?[0-9]*(?:[Ee]\ *-?\ *[0-9]+)?)\*\[?(\w+)\]?', m[1])
        #m=re.findall(r'(\w+) (\-\>)((-?\ *\.?[0-9]+\.?[0-9]*(?:[Ee]\ *-?\ *[0-9]+)?)\*\[?(\w+)\]?', a[0])
        #http://stackoverflow.com/questions/18152597/extract-scientific-number-from-string
        m[0]=m[0].strip()
        m[2]=float(m[2])
        for r in ar:
            mylist=chem_map.get(r[1])
            if mylist==None:
                mylist=[]

            mylist.append([m[0],float(r[0])])
            chem_map.update({r[1]:mylist})
        coefficients.update({m[0]:m[2]})

    print "\nConversion MAP:"
    for i in chem_map:
        print i+":\t"+str(chem_map.get(i))


    print "\nWRF multiplier MAP:"
    for i in coefficients:
        print i+":\t"+str(coefficients.get(i))
    print "\n"


def get_list_of_wrf_spec_by_merra_var(name):
    return chem_map.get(name)

def get_merra_vars():
    return chem_map.keys()

def get_wrf_vars():
    return coefficients.keys()

#initialise()
#print get_wrf_vars()
#print get_merra_vars()
#print "DU001="+str(get_list_of_wrf_spec_by_merra_name("DU001"))
#for t in get_list_of_wrf_spec_by_merra_var("DU001"):
#    print t[0]+" * "+str(t[1])
