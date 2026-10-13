import ROOT
import argparse
from loadHists import loadHists

parser  = argparse.ArgumentParser(description='Process ROOT files to fix zero bin contents in histograms.')
parser.add_argument("-i", "--infile", type=str, help='Input ROOT file', required=True)
args    = parser.parse_args()

infilename      = args.infile
outfilename     = infilename.replace(".root","_zerosFixed.root")

infile          = ROOT.TFile.Open(infilename, "OPEN")
outfile         = ROOT.TFile.Open(outfilename, "RECREATE")
thrInput        = 0.00000001 # if content less than this threshold
thrOutput       = 0.000001  # set value to this
histo_dict      = loadHists(infilename)

print(histo_dict.keys())

for histo_name,histo in histo_dict.items():
    tmp = histo.Clone(histo_name)
    for i in range(0, histo.GetNbinsX()+2):
        if histo.GetBinContent(i) < thrInput :
            print(f"Setting bin {i} of histogram {histo.GetName()} to {thrOutput} because it content is {histo.GetBinContent(i)} which is below the threshold {thrInput}")
            tmp.SetBinContent(i, thrOutput)
            tmp.SetBinError(i, thrOutput*0.99)
    
    outfile.cd()
    tmp.Write(histo_name, ROOT.TObject.kOverwrite)
    infile.cd()