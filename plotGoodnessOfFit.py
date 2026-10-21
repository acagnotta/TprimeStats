#!/usr/bin/env python3

import argparse
import json
import math
from pathlib import Path
import os, sys
import ROOT
import cmsstyle as CMS

ROOT.gROOT.SetBatch(True)

parser = argparse.ArgumentParser(description="Plot Combine goodness-of-fit results")
parser.add_argument("-i", "--input",        dest="input",                   default="gof.json",             help="Input JSON file with goodness-of-fit results")
parser.add_argument("-e", "--era",          dest="era",                     default="2022",                 help="Era to process, e.g. 2022, 2022EE, 2022+2023, etc.")
parser.add_argument("-j", "--jsonInput",    dest="jsonInput",               default="settings.json",        help="Settings JSON file")
parser.add_argument("-m", "--massPoint",    dest="massPoint",   type=int,   default=700,                    help="Tprime mass point")
parser.add_argument("--bins",               dest="bins",        type=int,   default=30,                     help="Number of bins for the histogram")
parser.add_argument("--x-max",              dest="x_max",       type=float, default=None,                   help="Upper x-axis bound; by default use a robust value derived from the toys")
parser.add_argument("--title",              dest="title",                   default="",                     help="Title of the plot")
args = parser.parse_args()

with open(args.input) as input_file:
    result      = json.load(input_file)["125.0"]
with open(args.jsonInput) as file:
    jsonInput   = json.load(file)

outputFolder    = Path(args.input).parent
era             = args.era
mass            = args.massPoint
lumi            = jsonInput["lumi_dict"][era]
toys            = result["toy"]
observed        = result["obs"][0]
if not toys:
    raise RuntimeError("The input file does not contain any pseudo-experiments")
if args.bins <= 0:
    raise ValueError("--bins must be positive")

p_value = sum(toy >= observed for toy in toys) / len(toys)
sorted_toys = sorted(toys)

def quantile(values, probability):
    position = (len(values) - 1) * probability
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return values[lower]
    fraction = position - lower
    return values[lower] * (1.0 - fraction) + values[upper] * fraction

q1 = quantile(sorted_toys, 0.25)
q3 = quantile(sorted_toys, 0.75)
robust_x_max = q3 + 3.0 * (q3 - q1)
x_min = min(0.0, min(toys), observed)
auto_x_max = math.ceil(robust_x_max)
if args.x_max is not None:
    x_max = args.x_max
elif observed <= 2.0 * auto_x_max:
    x_max = math.ceil(max(observed, robust_x_max))
else:
    x_max = auto_x_max
if x_max <= x_min:
    raise ValueError(f"The upper x-axis bound ({x_max}) must be greater than the lower bound ({x_min})")

hist = ROOT.TH1D(
    "gof_toys",
    "",
    args.bins,
    x_min,
    x_max,
)
for toy in toys:
    hist.Fill(toy)

# Fold extreme toys into the last visible bin so isolated outliers do not
# compress the central distribution into a single bin.
overflow = int(hist.GetBinContent(args.bins + 1))
if overflow:
    last_bin_content = hist.GetBinContent(args.bins) + overflow
    hist.SetBinContent(args.bins, last_bin_content)
    hist.SetBinError(args.bins, math.sqrt(last_bin_content))
    hist.SetBinContent(args.bins + 1, 0.0)
    hist.SetBinError(args.bins + 1, 0.0)

y_max = 1.35 * hist.GetMaximum()

CMS.SetExtraText("Work in progress")
CMS.SetLumi(lumi, run=None)
CMS.SetEnergy(13.6)
CMS.ResetAdditionalInfo()
canvas = CMS.cmsCanvas(
    "gof_canvas",
    x_min,
    x_max,
    0,
    y_max,
    "Goodness-of-fit test statistic",
    "Pseudo-experiments",
    square=True,
    iPos=0,
)

blue    = ROOT.TColor.GetColor("#5790fc")
red     = ROOT.TColor.GetColor("#e42536")
CMS.cmsDraw(hist, "HIST", lcolor=blue, lwidth=2, fcolor=blue, alpha=0.65)

observed_off_scale = observed < x_min or observed > x_max
edge_offset = 0.005 * (x_max - x_min)
observed_draw_x = min(max(observed, x_min + edge_offset), x_max - edge_offset)
observed_line = ROOT.TLine(observed_draw_x, 0, observed_draw_x, y_max)
CMS.cmsDrawLine(observed_line, lcolor=red, lstyle=ROOT.kDashed, lwidth=3)

legend_y_min = 0.72 if overflow else 0.77
legend = CMS.cmsLeg(0.48, legend_y_min, 0.90, 0.92, textSize=0.035)
legend.AddEntry(hist,           f"Pseudo-experiments ({len(toys)})",    "f")
observed_label = f"Observed = {observed:.3g}"
if observed_off_scale:
    observed_label += " (off-scale)"
legend.AddEntry(observed_line, observed_label, "l")
legend.AddEntry(ROOT.nullptr,   f"p-value = {p_value:.3f}",             "")
if overflow:
    legend.AddEntry(ROOT.nullptr, f"Overflow = {overflow}",             "")
legend.Draw()

# label = ROOT.TLatex()
# label.SetNDC()
# label.SetTextFont(42)
# label.SetTextSize(0.04)
# label.DrawLatex(0.19, 0.84, args.title)
# label.DrawLatex(0.58, 0.62, f"p-value = {p_value:.3f}")

print(f"Using {args.bins} bins in [{x_min:g}, {x_max:g}] with {overflow} overflow entries folded into the last bin; observed off-scale: {observed_off_scale}")
print(f"Saving plot to {outputFolder}/gof_plot.png and {outputFolder}/gof_plot.pdf")
CMS.SaveCanvas(canvas, f"{outputFolder}/gof_plot.png", False)
CMS.SaveCanvas(canvas, f"{outputFolder}/gof_plot.pdf")
