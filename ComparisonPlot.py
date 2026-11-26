import ROOT
import cmsstyle as CMS
from array import array
import numpy as np
import pandas as pd
from utils import run2_limits, theory_width5
from samples import sample_dict
ROOT.gROOT.SetBatch()

def read_txt(era):
    df = pd.read_csv(f"./{era}/expectedLimits.txt")
    return df


df_2022 = read_txt("2022tot")
df_run3 = read_txt("projectionRun3")

expected_2022 = df_2022["expected"]
expected_run3 = df_run3["expected"]

masses =df_2022["mass"]
th_width1 = [sample_dict[f"TprimeToTZ_{round(m*1000)}_2022"].sigma for m in masses]   # theory sigma (width 1%) of samples_TPrime.py, as in BrazilPlot/CompareLimits

th      = ROOT.TGraph(len(masses), array('d',masses),  array('d',th_width1))
thw5    = ROOT.TGraph(len(theory_width5["mass"]), array('d',theory_width5["mass"]),  array('d',theory_width5["xsec"]))
obsrun2 = ROOT.TGraph(len(run2_limits["mass"]), array('d',run2_limits["mass"]),  array('d',run2_limits["observed"]))
exp2022 = ROOT.TGraph(len(masses), array('d',masses),  array('d',expected_2022))
expRun3 = ROOT.TGraph(len(masses), array('d',masses),  array('d',expected_run3))

# Styling
# CMS.SetExtraText("Preliminary")
CMS.SetExtraText("Work in progress")
CMS.SetLumi("")
iPos = 0
canv_name = 'limitplot_root'
CMS.SetEnergy("13.6")
CMS.ResetAdditionalInfo()
y_str = "#sigma(pp#rightarrowTbq) #times BR(T#rightarrowtZ) [pb]"
canv = CMS.cmsCanvas(canv_name, min(masses)-0.05,max(masses)+0.05,min(th_width1) ,4,"T' mass[TeV]",y_str,square=CMS.kSquare,extraSpace=0.05,iPos=iPos)
canv.SetLogy()
CMS.cmsDraw(obsrun2, "L", lcolor = ROOT.TColor.GetColor("#832db6"), lwidth=3)
CMS.cmsDraw(exp2022, "L", lcolor = ROOT.TColor.GetColor("#5790fc"), lwidth=3, lstyle=ROOT.kDashed)
CMS.cmsDraw(expRun3, "L", lcolor = ROOT.TColor.GetColor("#f89c20"), lwidth=3, lstyle=ROOT.kDashed)
CMS.cmsDraw(th, "L", lcolor = ROOT.TColor.GetColor("#e42536"), lwidth=2)
CMS.cmsDraw(thw5, "L", lcolor = ROOT.kBlue+2, lwidth=2)

# canv.SetLogy()
leg = CMS.cmsLeg(0.3, 0.90 - 0.05 * 4, 0.95, 0.90, textSize=0.04)
leg.AddEntry(exp2022, "expected 2022 (34.36 fb^{-1})","L")
leg.AddEntry(expRun3, "expected 2022-2024 (184 fb^{-1})","L")
leg.AddEntry(obsrun2, "observed Run-II (137 fb^{-1})","L")
leg.AddEntry(th, "#sigma(NLO), Singlet T, #Gamma/m_{T}<0.01","L")
leg.AddEntry(thw5, "#sigma(NLO), Singlet T, #Gamma/m_{T}=0.05","L")

CMS.SaveCanvas(canv, "./ComparisonExpectedLimits.png", False)
CMS.SaveCanvas(canv, "./ComparisonExpectedLimits.pdf")