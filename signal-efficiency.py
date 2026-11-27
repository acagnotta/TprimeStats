import ROOT
import cmsstyle as CMS
from array import array
import argparse
import json
import os
from samples import *
from utils import unpackLabel, getLumi
ROOT.gROOT.SetBatch()

# Signal acceptance x efficiency vs T mass: Integral(0, N+1) of the signal histogram in each region / (sigma * L)
# One plot per top category, with the regions listed in "plots" (TBNXT = Tight but not XT)
red, blue = "#bd1f01", "#3f90da"
plots = {  # top category -> {region: (legend label, color, marker)}
    "Resolved": {
        "SRTopRes0fjetsBtagMedium":             ("TBNXT, 0 forward jets",    red,  20),
        "SRTopResatleast1fjetsBtagMedium":      ("TBNXT, #geq1 forward jet", red,  22),
        "SRTop0fjetsResXTBtagMedium":           ("XT, 0 forward jets",       blue, 20),
        "SRTopatleast1fjetsResXTBtagMedium":    ("XT, #geq1 forward jet",    blue, 22),
    },
    "Mixed": {
        "SRTopMix0fjetsBtagMedium":             ("TBNXT, 0 forward jets",    red,  20),
        "SRTopMixatleast1fjetsBtagMedium":      ("TBNXT, #geq1 forward jet", red,  22),
        "SRTop0fjetsMixXTBtagMedium":           ("XT, 0 forward jets",       blue, 20),
        "SRTopatleast1fjetsMixXTBtagMedium":    ("XT, #geq1 forward jet",    blue, 22),
    },
    "Merged": {
        "SRTopMer0fjetsBtagMedium":             ("TBNXT, 0 forward jets",    red,  20),
        "SRTopMeratleast1fjetsBtagMedium":      ("TBNXT, #geq1 forward jet", red,  22),
        "SRTop0fjetsMerXTBtagMedium":           ("XT, 0 forward jets",       blue, 20),
        "SRTopatleast1fjetsMerXTBtagMedium":    ("XT, #geq1 forward jet",    blue, 22),
    },
}

parser = argparse.ArgumentParser(description="Signal acceptance x efficiency vs T mass")
parser.add_argument("-e", "--era",          default="2024",     help="Era, e.g. 2024")
parser.add_argument("-i", "--inputFolder",  required=True,      help="Folder with histo<era>.root, where the plots are also saved")
opt = parser.parse_args()

# lumi per era from the reference settings.json of the repo
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")) as f:
    lumi_dict = json.load(f)["lumi_dict"]

era         = opt.era
folder      = opt.inputFolder.rstrip("/")
lumi        = getLumi(lumi_dict, era)
regions     = [r for topCatRegions in plots.values() for r in topCatRegions]
firstEra    = era.split("+")[0]

##### Efficiency (%) for each region and mass #####
inFile  = ROOT.TFile.Open(f"{folder}/histo{era}.root")
# signals in the file, from the names hist_TprimeToTZ_<mass>_<region>_nominal
signals = sorted({"_".join(k.GetName().split("_")[1:3]) for k in inFile.GetListOfKeys() if k.GetName().startswith("hist_TprimeToTZ_")}, key=lambda s: unpackLabel(s)[0])
masses  = [unpackLabel(s)[0] for s in signals]
eff     = {r: [] for r in regions}
for s in signals:
    sigma_fb = sample_dict[f"{s}_{firstEra}"].sigma * 1e3   # pb -> fb, lumi is in fb^-1
    for r in regions:
        h = inFile.Get(f"hist_{s}_{r}_nominal")
        eff[r].append(100 * h.Integral(0, h.GetNbinsX() + 1) / (sigma_fb * lumi))
inFile.Close()

print(f"{'mass [TeV]':<40}" + "".join(f"{m:>8.1f}" for m in masses))
for r in regions:
    print(f"{r:<40}" + "".join(f"{e:>8.3f}" for e in eff[r]))
print(f"{'SUM':<40}" + "".join(f"{sum(eff[r][i] for r in regions):>8.3f}" for i in range(len(masses))))

##### Plots #####
CMS.SetExtraText("Work in Progress")
CMS.SetLumi(lumi, run="Run 3", round_lumi=3)
CMS.SetEnergy(13.6)
CMS.ResetAdditionalInfo()

for topCat, topCatRegions in plots.items():
    graphs = [(ROOT.TGraph(len(masses), array("d", masses), array("d", eff[r])), color, marker, label) for r, (label, color, marker) in topCatRegions.items()]
    y_max  = 2.0 * max(max(eff[r]) for r in topCatRegions)
    canv   = CMS.cmsCanvas(f"signalEfficiency_{topCat}", min(masses) - 0.1, max(masses) + 0.1, 0, y_max, "m_{T} [TeV]", "Acceptance #times Efficiency (%)", square=True, extraSpace=0.12, iPos=11, yTitOffset=1.9)
    for frame in [p for p in canv.GetListOfPrimitives() if p.GetName().startswith("hframe")]:  # cmsCanvas redraws the axes with copies of hframe
        frame.GetXaxis().SetNdivisions(505)
    leg   = CMS.cmsLeg(0.52, 0.56, 0.93, 0.76, textSize=0.035)
    leg.SetHeader(f"{topCat}, #Gamma/m_{{T}} = 1%")
    for g, color, marker, label in graphs:
        CMS.cmsDraw(g, "P", marker=marker, msize=1.2, mcolor=ROOT.TColor.GetColor(color))
        leg.AddEntry(g, label, "P")
    CMS.SaveCanvas(canv, f"{folder}/signalEfficiency_{topCat}_{era}.png", False)
    CMS.SaveCanvas(canv, f"{folder}/signalEfficiency_{topCat}_{era}.pdf")
