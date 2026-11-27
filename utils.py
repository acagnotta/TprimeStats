def unpackLabel(l,verbose=0):#function to extract the model from the label
    mass = ""
    model = ""

    if "TBDM" in l or "TTDM"in l or "TWDM" in l:
        mass=0.001*int((l.split("mPhi")[1]).split("_mChi")[0])
        model=(l.split("_mPhi")[0])
    if "Tprime" in l:
        mass=0.001*int((l.split("TprimeToTZ_")[1]))
        model=("TprimeToTZNW")
    if(verbose>0):print(f"label: {l}, mass: {mass}, model: {model}" )    
    return mass,model

def getLumi(lumi_dict, era):#total luminosity of an era, also for combined eras like 2023+2024
    return sum(lumi_dict[e] for e in era.split("+"))

# 95% CL upper limits of the Full Run 2 T' -> tZ search (137 fb^-1), T width 1% of the mass: masses in TeV, sigma x BR in pb
# Analysis: CMS-B2G-19-004, JHEP 05 (2022) 093, doi:10.1007/JHEP05(2022)093 (INSPIRE 2006491)
# HEPData: https://www.hepdata.net/record/ins2006491?version=1&table=Figure%208a (doi:10.17182/hepdata.100426.v1/t37): observed and
# expected 95% CL upper limits for a T with width 0.01 x mass (the 0.6 TeV point of the table is not used here)
#   "expected": median expected limit, "observed": observed limit
# The theory cross section for width 1% is sigma_TprimeToTZ_13TeV in samples_TPrime.py (sample_dict[...].sigma), equal to
# the first "Singlet cross section" curve of Figure 8a within its rounding
run2_limits = {
    "mass":     [0.7,     0.8,     0.9,     1.0,     1.1,     1.2,     1.3,     1.4,     1.5,     1.6,     1.7,     1.8    ],
    "expected": [0.36702, 0.17070, 0.10685, 0.07576, 0.05272, 0.03193, 0.02376, 0.01967, 0.01859, 0.01639, 0.01372, 0.01271],
    "observed": [0.21201, 0.09651, 0.07699, 0.07321, 0.06227, 0.04283, 0.04972, 0.04938, 0.03669, 0.02263, 0.01830, 0.01505],
}

# theory cross section of a singlet T with width 5% of the mass, in pb: second "Singlet cross section" curve of the same table
# (https://www.hepdata.net/record/ins2006491?version=1&table=Figure%208a); the table does not state its width: 5% from the ratio ~5 to the 1% curve
theory_width5 = {
    "mass": [0.7,    0.8,    0.9,    1.0,    1.1,    1.2,    1.3,    1.4,    1.5,    1.6,    1.7,    1.8   ],
    "xsec": [0.3877, 0.2045, 0.1137, 0.0659, 0.0370, 0.0246, 0.0156, 0.0101, 0.0067, 0.0045, 0.0031, 0.0021],
}
