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

# expected limit of the Full Run 2 T' -> tZ search (137 fb^-1): masses in TeV, cross section x BR in pb
run2_expected_masses    = [0.7,     0.8,     0.9,     1.0,      1.1,     1.2,     1.3,     1.4,     1.5,     1.6,      1.7,      1.8]
run2_expected_xsec      = [0.36602, 0.17070, 0.10685, 0.07576,  0.05272, 0.03193, 0.02376, 0.01967, 0.01859, 0.016390, 0.013720, 0.012710 ]
