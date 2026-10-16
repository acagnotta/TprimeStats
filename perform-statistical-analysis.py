import subprocess
import json
import argparse
import os
import shutil

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-e', '--era',          type=str,               default='2023',             help='Era of the datacard')
parser.add_argument('-j', '--jsonInput',    type=str,               default='settings.json',    help='Settings JSON file')
parser.add_argument('-p', '--positive',     action="store_true",                                help='Fix zero bin contents in histograms')
parser.add_argument("-u", "--unblind",      action="store_true",                                help="Use data instead of the background sum")
parser.add_argument('-s', '--suffix',       type=str,               default='',                 help='Suffix labelling the whole run (e.g. histo2023_<suffix>.root)')
args = parser.parse_args()

era             = args.era
unblind         = "--unblind" if args.unblind else ""
histo_suffix    = args.suffix                                                       # suffix of histo<era>_<suffix>.root
suffix          = "_".join(s for s in [args.suffix, "zerosFixed" if args.positive else ""] if s)   # suffix of the whole run

with open(args.jsonInput) as file:
    print("Opening JSON file {}".format(args.jsonInput))
    jsoninput   = json.load(file)

output_dir      = jsoninput["dc-folder"][era].rstrip("/")
massPoints      = [signal.split('_')[-1] for signal in jsoninput["processes"]["signals"]]

# Save a copy of the settings and the list of commands in the output folder, to be able to rerun exactly the same analysis
os.makedirs(output_dir, exist_ok=True)
settings_file   = f"{output_dir}/settings{f'_{suffix}' if suffix else ''}.json"
commands_file   = f"{output_dir}/commands{f'_{suffix}' if suffix else ''}.sh"
shutil.copy(args.jsonInput, settings_file)
with open(commands_file, "w") as f:
    f.write(f"cd {os.getcwd()}\n")

suffix_opt      = f"--suffix {suffix}" if suffix else ""

def run(cmd):
    print(f"Running: {cmd}")
    with open(commands_file, "a") as f:
        f.write(cmd + "\n")
    subprocess.run(cmd, shell=True, check=True)


run(f"python3 CollectHistos.py -e {era} -j {settings_file} --addSyst {f'--suffix {histo_suffix}' if histo_suffix else ''} {unblind}")

if args.positive:
    run(f"python3 makePositiveHistos.py -i {output_dir}/histo{era}{f'_{histo_suffix}' if histo_suffix else ''}.root")

run(f"python3 CreateDatacards.py -e {era} -j {settings_file} --addSyst --addMCStat {suffix_opt} {unblind}")

for mass in massPoints:
    run(f"python3 doImpacts.py -e {era} -m {mass} -j {settings_file} {suffix_opt}")
    run(f"python3 doGoodnessOfFit.py -e {era} -m {mass} -j {settings_file} -t 500 -s 123456 {suffix_opt}")
    run(f"python3 doBiasTest.py -e {era} -m {mass} -j {settings_file} -t 500 {suffix_opt}")
