import numpy as np
from scipy.integrate import quad

#this routine calculates volume under the log-normal distribution
def integrand(x):
    return (4.0*np.pi*(x**3)/3.0)*(np.exp(-(np.log(x) - mu)**2 / (2 * sigma**2))/(x * sigma * np.sqrt(2 * np.pi)))


#============================================================
# Taken from module_data_sorgam.F
# initial mean diameter for Aitken mode [ mu ]    
dginin=0.01
# initial sigma-G for Aitken mode                 
sginin=1.70

# initial mean diameter for accumulation mode [ mu ]
dginia=0.07
# initial sigma-G for accumulation mode          
sginia=2.00


FRAC2Aitken = 0.25   #Fraction of modal mass in Aitken mode
mass_so4i   = FRAC2Aitken #masses into modal Aitken mode
mass_so4j   = (1.0-FRAC2Aitken) # masses into modal accumulation mode

dlo=0.0390625
dhi=10.0
nbin_o=8
#============================================================

fr8b_aem_mosaic_i=np.zeros(nbin_o)
fr8b_aem_mosaic_j=np.zeros(nbin_o)
fr8b_sulf_mosaic  =np.zeros(nbin_o)

dlo_sectm=np.zeros(nbin_o)
dhi_sectm=np.zeros(nbin_o)

#============================================================
#MOSAIC bins ranges
xlo = np.log( dlo )
xhi = np.log( dhi )
dxbin = (xhi - xlo)/nbin_o
for n in range(1,nbin_o+1):
    dlo_sectm[n-1] = np.exp( xlo + dxbin*(n-1))
    dhi_sectm[n-1] = np.exp( xlo + dxbin*n )
    #print ("{:.6f}".format(dlo_sectm[n-1]),"{:.4f}".format(dhi_sectm[n-1]))

#============================================================
# Mass fractions for Aitken mode
mu = np.log(dginin)
sigma = np.log(sginin)

#total volume under the curve
total_volume, err = quad(integrand, 0, 100) 

for n in range(0,nbin_o):
  integ, err = quad(integrand, dlo_sectm[n], dhi_sectm[n])
  fr8b_aem_mosaic_i[n]=integ/total_volume

#print ("\nSulfate Aitken mode mass redistribution:")
#print (fr8b_aem_mosaic_i*mass_so4i)

#============================================================
# Mass fractions for Aitken mode
mu = np.log(dginia)
sigma = np.log(sginia)

#total volume under the curve
total_volume, err = quad(integrand, 0, 100) 

for n in range(0,nbin_o):
  integ, err = quad(integrand, dlo_sectm[n], dhi_sectm[n])
  fr8b_aem_mosaic_j[n]=integ/total_volume

#print ("\nSulfate accumulation mode mass redistribution:")
#print (fr8b_aem_mosaic_j*mass_so4j)


print ("\nSulfate mass redistribution")
fr8b_sulf_mosaic=fr8b_aem_mosaic_i*mass_so4i+fr8b_aem_mosaic_j*mass_so4j
print (fr8b_sulf_mosaic)
