import subprocess
import os
import optparse
import json

usage  = 'python3 doImpacts.py'
parser = optparse.OptionParser(usage)
parser.add_option('-e', '--era',        dest='era',         type=str,   default = '2022',                                   help='Please enter the era of the datacard, if not specified the code will take the era 2022')
parser.add_option('-m', '--massPoint',                      type=int,   default = 700,                                      help='Please enter the mass point of the datacard, if not specified the code will take the mass point 700')
parser.add_option("-j", "--jsonInput",                                  default = "settings.json",                          help="Settings JSON file")
parser.add_option(      '--FitOption',  dest='FitOption',   type=str,   default = "--robustFit 1 -t -1 --setParameterRanges r=-100,100",  help='Please enter the fit option, if not specified the code will take the fit option -t -1')
(opt, args) = parser.parse_args()

with open(opt.jsonInput) as file:
    jsoninput = json.load(file)

era             = opt.era
mass            = str(opt.massPoint)
FitOption       = opt.FitOption
dc_folder       = jsoninput["dc-folder"][era]
impact_dir      = f"{dc_folder}/TprimeToTZ_{mass}/impacts/"


print("Running impacts for era: {}, mass: {}, FitOption: {}".format(era, mass, FitOption))

if not os.path.exists(impact_dir):
    os.makedirs(impact_dir)
# subprocess.run("pwd")
# Change working directory for subsequent commands by using cwd parameter in subprocess.run

subprocess.run(f"text2workspace.py ../TprimeToTZ_{mass}.txt -m 125 -o workspace_TprimeToTZ_{mass}.root",                     shell=True, check=True, cwd=impact_dir)
subprocess.run(f"combineTool.py -M Impacts -d workspace_TprimeToTZ_{mass}.root -m 125 --doInitialFit {FitOption}",           shell=True, check=True, cwd=impact_dir)
subprocess.run(f"combineTool.py -M Impacts -d workspace_TprimeToTZ_{mass}.root -m 125 --doFit {FitOption} --parallel 50",    shell=True, check=True, cwd=impact_dir)
subprocess.run(f"combineTool.py -M Impacts -d workspace_TprimeToTZ_{mass}.root -m 125 -o impact.json",                       shell=True, check=True, cwd=impact_dir)
subprocess.run(f"plotImpacts.py -i impact.json -o impacts --summary",                                                        shell=True, check=True, cwd=impact_dir)