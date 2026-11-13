import ROOT
import cmsstyle as CMS
from array import array
from samples import *
import argparse
import glob
import json
import os
from utils import unpackLabel, getLumi, run2_expected_masses, run2_expected_xsec
ROOT.gROOT.SetBatch()

usage = "python3 CompareLimits.py -i <dc-folder A>/Limits_2024_<suffix>.json <dc-folder B>/Limits_2024_<suffix>.json [-l labelA labelB] [-o CompareLimits]"
parser = argparse.ArgumentParser(description="Compare the expected limits (median) of several runs, together with the Full Run 2 expected limit and the theory cross section", usage=usage)
parser.add_argument('-i', '--inputs',       type=str,   nargs='+',  required=True,          help='Limits_<era>_<suffix>.json files written by RunLimits.py')
parser.add_argument('-l', '--labels',       type=str,   nargs='+',  default=[],             help='Legend labels, one per input (default: name of the folder of each json)')
parser.add_argument('-o', '--output',       type=str,               default='CompareLimits',help='Output file name without extension (.png and .pdf are written)')
parser.add_argument('--ymin',               type=float,             default=1e-3,           help='Minimum of the y axis [pb]')
parser.add_argument('--ymax',               type=float,             default=None,           help='Maximum of the y axis [pb] (default: 50 x the largest value)')
parser.add_argument('--rectangular',        action='store_true',                            help='Rectangular canvas instead of the square one')
opt = parser.parse_args()

if opt.labels and len(opt.labels) != len(opt.inputs):
    parser.error(f"{len(opt.labels)} labels for {len(opt.inputs)} inputs")

def eraFromName(path):
    # Limits_<era>_<suffix>.json, as written by RunLimits.py
    return os.path.basename(path).removeprefix("Limits_").removesuffix(".json").split("_")[0]

eras        = [eraFromName(f) for f in opt.inputs]
labels      = opt.labels or [os.path.basename(os.path.dirname(os.path.abspath(f))) + (f" ({era})" if len(set(eras)) > 1 else "") for f, era in zip(opt.inputs, eras)]
colors      = [CMS.p10.kBlue, CMS.p10.kYellow, CMS.p10.kViolet, CMS.p10.kGreen, CMS.p10.kOrange, CMS.p10.kCyan, CMS.p10.kBrown, CMS.p10.kGray, CMS.p10.kAsh]

# expected limit in pb = median r x theory cross section of each mass
graphs, all_y = [], []
for f, era in zip(opt.inputs, eras):
    with open(f) as file:
        limits = json.load(file)
    masses, xsec, y = [], [], []
    for signal, values in limits.items():
        mass, model = unpackLabel(signal)
        sigma       = sample_dict[f"{signal}_{era.split('+')[0]}"].sigma
        masses.append(mass)
        xsec.append(sigma)
        y.append(values[2] * sigma)
    graphs.append(ROOT.TGraph(len(masses), array('d', masses), array('d', y)))
    all_y += y
    print(f"{f}: era {era}, " + ", ".join(f"{m:.1f} TeV {v:.3g} pb" for m, v in zip(masses, y)))
    if len(graphs) == 1:
        th = ROOT.TGraph(len(masses), array('d', masses), array('d', xsec))   # theory curve from the first input
        x_min, x_max = min(masses), max(masses)
        all_y += xsec

exprun2 = ROOT.TGraph(len(run2_expected_masses), array('d', run2_expected_masses), array('d', run2_expected_xsec))
all_y  += run2_expected_xsec

# luminosity in the label only when all inputs are the same era; lumi_dict from the settings saved next to the json
lumi = ""
settings = glob.glob(f"{os.path.dirname(os.path.abspath(opt.inputs[0]))}/settings*.json")
if len(set(eras)) == 1 and settings:
    with open(settings[0]) as file:
        lumi = getLumi(json.load(file)["lumi_dict"], eras[0])

# Styling
CMS.SetExtraText("Work in progress")
iPos = 11
CMS.SetLumi(lumi, run="Run 3", round_lumi=3)
CMS.SetEnergy(13.6)
CMS.ResetAdditionalInfo()
y_str = "#sigma(pp#rightarrowTbq) #times BR(T#rightarrowtZ) [pb]"
canv = CMS.cmsCanvas("comparelimits", x_min-0.05, x_max+0.05, opt.ymin, opt.ymax or max(all_y)*50, "T' mass [TeV]", y_str, square=not opt.rectangular, extraSpace=0.05, iPos=iPos)
canv.SetLogy()
if opt.rectangular:
    CMS.GetCmsCanvasHist(canv).GetYaxis().SetTitleOffset(1.15)   # the y title overlaps the 10^n labels otherwise

leg = CMS.cmsLeg(0.50, 0.89 - 0.037*(len(graphs)+3), 0.93, 0.89, textSize=0.028)
leg.SetHeader("95% CL expected limits")
for g, label, color in zip(graphs, labels, colors):
    CMS.cmsDraw(g, "LP", marker=20, msize=0.8, mcolor=color, lcolor=color, lwidth=2)
    leg.AddEntry(g, label, "LP")
CMS.cmsDraw(exprun2, "L", lcolor=ROOT.kBlack, lwidth=2, lstyle=ROOT.kDashed)
leg.AddEntry(exprun2, "Full Run 2 (137 fb^{-1})", "L")
CMS.cmsDraw(th, "L", lcolor=ROOT.TColor.GetColor("#bd1f01"), lwidth=2)
leg.AddEntry(th, "#sigma(NLO), Singlet T, #Gamma/m_{T}<0.01", "L")

CMS.CMS_lumi(canv, iPos)
CMS.SaveCanvas(canv, f"{opt.output}.png", False)
CMS.SaveCanvas(canv, f"{opt.output}.pdf")
