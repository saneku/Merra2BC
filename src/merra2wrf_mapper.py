
import re
from . import config

# Mapping between MERRA2 species and output species.
chem_map={}                         # MERRA variable -> output species map
coefficients={}                     # output multiplier map
constant_map={}                     # output species -> constant value in output units


def initialise():
    chem_map.clear()
    coefficients.clear()
    constant_map.clear()

    for a in config.spc_map:
        m=re.split('->|;',a)
        if len(m) < 3:
            raise ValueError("Invalid mapping line: " + str(a))

        out_name=m[0].strip()
        rhs=m[1].strip()
        multiplier=float(m[2])
        ar=re.findall(r'(-?\ *\.?[0-9]+\.?[0-9]*(?:[Ee]\ *?[-+]?\ *[0-9]+)?)\*\[?(\w+)\]?', rhs)

        if ar:
            for r in ar:
                mylist=chem_map.get(r[1])
                if mylist==None:
                    mylist=[]

                mylist.append([out_name,float(r[0])])
                chem_map.update({r[1]:mylist})
        else:
            constant_map.update({out_name:float(rhs)*multiplier})

        coefficients.update({out_name:multiplier})

    print ("\nConversion MAP:")
    for i in chem_map:
        print (i+":\t"+str(chem_map.get(i)))

    if constant_map:
        print ("\nConstant MAP:")
        for i in constant_map:
            print (i+":\t"+str(constant_map.get(i)))

    print ("\nWRF multiplier MAP:")
    for i in coefficients:
        print (i+":\t"+str(coefficients.get(i)))
    print ("\n")


def get_list_of_wrf_spec_by_merra_var(name):
    return chem_map.get(name)

def get_merra_vars():
    return chem_map.keys()

def get_wrf_vars():
    return coefficients.keys()

def get_constant_vars():
    return constant_map.keys()

def get_constant_map():
    return constant_map

def is_constant_var(name):
    return name in constant_map
