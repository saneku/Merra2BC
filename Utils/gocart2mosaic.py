# Utility to calculate mass and number redistribution from GOCART to MOSAIC
# CBMZ-MOSAIC_8bins SO2, Sulf, O3, CO, DUST and Sea salt (NaCl).
# so4_a0X,oc_a0X,bc_a0X still need to be done
# Alexander Ukhov (KAUST) 13 Oct. 2020

import numpy as np
from pandas import *

ndust=5
nsalt=5
nbin_o=8

mw_na_aer=22.989769
mw_cl_aer=35.453
fracna = mw_na_aer / (mw_na_aer + mw_cl_aer)
fraccl = 1.0 - fracna

dustfrc_goc8bin_ln=np.zeros((ndust,nbin_o))
saltfrc_goc8bin_ln=np.zeros((nsalt,nbin_o))
na_frc_goc8bin_ln=np.zeros((nsalt,nbin_o))
cl_frc_goc8bin_ln=np.zeros((nsalt,nbin_o))

#See Sulfate_redistribution.py script
fr8b_sulf_mosaic=[5.75408980e-02, 1.16135472e-01, 2.64759054e-01, 2.46168555e-01,9.11155077e-02, 1.33280318e-02, 7.61932320e-04, 1.68197832e-05]

########
dlo_sectm=np.zeros(nbin_o)
dhi_sectm=np.zeros(nbin_o)
dcen_sect=np.zeros(nbin_o)
dust_mass1part=np.zeros(nbin_o)
salt_mass1part=np.zeros(nbin_o)
sulf_mass1part=np.zeros(nbin_o)

dlo=0.0390625
dhi=10.0

print "MOZAIC bins (diameter), (mu)\t Center of the bin, (cm)\t Mass of dust particle, (kg)\t Mass of sea salt particle, (kg)\t Mass of sulf particle, (kg)"
xlo = np.log( dlo )
xhi = np.log( dhi )
dxbin = (xhi - xlo)/nbin_o
for n in range(1,nbin_o+1):
    dlo_sectm[n-1] = np.exp( xlo + dxbin*(n-1))
    dhi_sectm[n-1] = np.exp( xlo + dxbin*n )
    dcen_sect[n-1] = np.sqrt( dlo_sectm[n-1]*dhi_sectm[n-1])

    #convert center of bins from microns to cm
    dcen_sect[n-1] = dcen_sect[n-1]*1.0e-4
    if (n <= 5):
        densdust=2.5
    if (n > 5 ):
        densdust=2.65

    #sea salt dry particle density (g/cm3)
    #effect of water uptake is not accounted
    saltdens = 2.165

    #Sulf particle density (g/cm3)
    #effect of water uptake is not accounted
    sulfdens = 1.8


    #mass of a single dust particle in kg, density of dust ~2.5 g cm-3               
    dust_mass1part[n-1]=0.523598*(dcen_sect[n-1]**3)*densdust*1.0e-3

    #mass of a single sea salt particle in kg, density 2.165 g cm-3               
    salt_mass1part[n-1]=0.523598*(dcen_sect[n-1]**3)*saltdens*1.0e-3

    #mass of a single sulf particle in kg, density 1.8 g cm-3               
    sulf_mass1part[n-1]=0.523598*(dcen_sect[n-1]**3)*sulfdens*1.0e-3

    print '{:0.3f}'.format(dlo_sectm[n-1])+"-"+'{:0.3f}'.format(dhi_sectm[n-1])+"\t\t\t\t"+'{:0.3e}'.format(dcen_sect[n-1])+"\t\t\t"+'{:0.3e}'.format(dust_mass1part[n-1])+"\t\t\t"+'{:0.3e}'.format(salt_mass1part[n-1])+"\t\t\t\t"+'{:0.3e}'.format(sulf_mass1part[n-1])


#these are MOZAIC SIZES!!!
#dlo_sectm=np.array([0.039062474, 0.07812498, 0.15624990, 0.31249994, 0.62499959, 1.25, 2.5, 5.0])
#dhi_sectm=np.array([0.078124984, 0.15624990, 0.31249994, 0.62499959, 1.25 , 2.5, 5.0, 10.0])


########
#reff_dust=np.array([0.73,1.4,2.4,4.5,8.0])
ra_gocart_dust=np.array([0.1,1.0,1.8,3.0,6.0])
rb_gocart_dust=np.array([1.0,1.8,3.0,6.0,10.0])

ra_gocart_salt=np.array([0.03,0.1,0.5,1.5,5.0])
rb_gocart_salt=np.array([0.10,0.5,1.5,5.0,10.0])


#Dust
for m in range(0,ndust):  # loop over dust size bins
	dlogoc = ra_gocart_dust[m]*2.0  # low diameter limit
	dhigoc = rb_gocart_dust[m]*2.0  # hi diameter limit

	for n in range(0,nbin_o):
		dustfrc_goc8bin_ln[m,n]=max(0.0,min(np.log(dhi_sectm[n]),np.log(dhigoc)) - max(np.log(dlogoc),np.log(dlo_sectm[n])))/(np.log(dhigoc)-np.log(dlogoc))

# Need to fill oin_a01 and oin_a02.
# Let's assume that oin_a01 is 15 times less than oin_a03
# and oin_a02 is 5 times less than oin_a03
dustfrc_goc8bin_ln[0,0]=dustfrc_goc8bin_ln[0,2]/15.0
dustfrc_goc8bin_ln[0,1]=dustfrc_goc8bin_ln[0,2]/5.0

print "----------------"
print "\nDust mass redistribution"
#print DataFrame(dustfrc_goc8bin_ln)
#print "----------------"

for n in range(0,nbin_o):
    s=""
    for m in range(0,ndust):
        if dustfrc_goc8bin_ln[m,n]>0:
            if s!="":
                s=s+"+"
            s=s+"{:.5f}".format(dustfrc_goc8bin_ln[m,n])+"*[DU00"+str(m+1)+"]"

    if s!="":
        print "'oin_a0"+str(n+1)+"->"+s+";1.e9',"
    else:
        print "'oin_a0"+str(n+1)+"->0.0*[DU001];1.e9',"


for n in range(0,nbin_o):
    dustfrc_goc8bin_ln[:,n]=dustfrc_goc8bin_ln[:,n]/dust_mass1part[n]

#print "Dust number"
#print DataFrame(dustfrc_goc8bin_ln)
#print "----------------"



#Sea salt (Na+Cl)
for m in range(0,nsalt):  # loop over salt size bins
	dlogoc = ra_gocart_salt[m]*2.0  # low diameter limit
	dhigoc = rb_gocart_salt[m]*2.0  # hi diameter limit

	for n in range(0,nbin_o):
		saltfrc_goc8bin_ln[m,n]=max(0.0,min(np.log(dhi_sectm[n]),np.log(dhigoc)) - max(np.log(dlogoc),np.log(dlo_sectm[n])))/(np.log(dhigoc)-np.log(dlogoc))

#print "Sea salt mass redistribution"
#print DataFrame(saltfrc_goc8bin_ln)
#print "----------------"

cl_frc_goc8bin_ln=fraccl*saltfrc_goc8bin_ln
na_frc_goc8bin_ln=fracna*saltfrc_goc8bin_ln

print "\nNa mass redistribution"
#print DataFrame(na_frc_goc8bin_ln)
#print "----------------"

for n in range(0,nbin_o):
    s=""
    for m in range(0,nsalt):
        if na_frc_goc8bin_ln[m,n]>0:
            if s!="":
                s=s+"+"
            s=s+"{:.6f}".format(na_frc_goc8bin_ln[m,n])+"*[SS00"+str(m+1)+"]"

    if s!="":
        print "'na_a0"+str(n+1)+"->"+s+";1.e9',"
    else:
        print "'na_a0"+str(n+1)+"->0.0*[SS001];1.e9',"


for n in range(0,nbin_o):
    na_frc_goc8bin_ln[:,n]=na_frc_goc8bin_ln[:,n]/salt_mass1part[n]


#print "Na number"
#print DataFrame(na_frc_goc8bin_ln)
#print "----------------"



print "\nCl mass redistribution"
#print DataFrame(cl_frc_goc8bin_ln)
#print "----------------"

for n in range(0,nbin_o):
    s=""
    for m in range(0,nsalt):
        if cl_frc_goc8bin_ln[m,n]>0:
            if s!="":
                s=s+"+"
            s=s+"{:.6f}".format(cl_frc_goc8bin_ln[m,n])+"*[SS00"+str(m+1)+"]"

    if s!="":
        print "'cl_a0"+str(n+1)+"->"+s+";1.e9',"
    else:
        print "'cl_a0"+str(n+1)+"->0.0*[SS001];1.e9',"

for n in range(0,nbin_o):
    cl_frc_goc8bin_ln[:,n]=cl_frc_goc8bin_ln[:,n]/salt_mass1part[n]

#print "Cl number"
#print DataFrame(cl_frc_goc8bin_ln)
#print "----------------"

print "\nSulfate mass redistribution"
for n in range(0,nbin_o):
    s=""
    s=s+"{:.6f}".format(fr8b_sulf_mosaic[n])+"*[SO4]"
    print "'sulf_a0"+str(n+1)+"->"+s+";1.e9',"

#print "Sulf number"
#print "----------------"

for n in range(0,nbin_o):
    fr8b_sulf_mosaic[n]=fr8b_sulf_mosaic[n]/sulf_mass1part[n]


print "\nTotal number redistribution"
#Total number concentration (#/kg)
for n in range(0,nbin_o):
    s=""
    for m in range(0,ndust):
        #print [m,n]
        if dustfrc_goc8bin_ln[m,n]>0:
            if s!="":
                s=s+"+"
            s=s+"{0:1.3e}".format(dustfrc_goc8bin_ln[m,n])+"*[DU00"+str(m+1)+"]"
        
        if na_frc_goc8bin_ln[m,n]>0:
            if s!="":
                s=s+"+"
            s=s+"{0:1.3e}".format(na_frc_goc8bin_ln[m,n]+cl_frc_goc8bin_ln[m,n])+"*[SS00"+str(m+1)+"]"

    s=s+"+"
    s=s+"{0:1.3e}".format(fr8b_sulf_mosaic[n])+"*[SO4]"

        #if cl_frc_goc8bin_ln[m,n]>0:
        #    if s!="":
        #        s=s+"+"
        #    s=s+"{0:1.3e}".format(cl_frc_goc8bin_ln[m,n])+"*[SS00"+str(m+1)+"]"

    print "'num_a0"+str(n+1)+"->"+s+";1',"
