import subprocess
import json
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-e', '--era',          type=str,               default='2023',             help='Era of the datacard')
parser.add_argument('-j', '--jsonInput',    type=str,               default='settings.json',    help='Settings JSON file')
parser.add_argument('-p', '--positive',     action="store_true",                                help='Fix zero bin contents in histograms')
parser.add_argument("-u", "--unblind",      action="store_true",                                help="Use data instead of the background sum")
args = parser.parse_args()

era             = args.era
settings_file   = args.jsonInput
unblind         = args.unblind
positive        = args.positive
suffix          = "zerosFixed" if positive else ""

with open(settings_file) as file:
    print("Opening JSON file {}".format(settings_file))
    jsoninput   = json.load(file)


output_dir      = jsoninput["dc-folder"][era]
massPoints      = [signal.split('_')[-1] for signal in jsoninput["processes"]["signals"]]


cmd = f"python3 CollectHistos.py -e {era} -j {settings_file} --addSyst {'--unblind' if unblind else ''}"
subprocess.run(cmd, shell=True, check=True)

if positive:
    cmd = f"python3 makePositiveHistos.py -i {output_dir}/histo{era}.root"
    subprocess.run(cmd, shell=True, check=True)

cmd = f"python3 CreateDatacards.py -e {era} -j {settings_file} --addSyst --addMCStat --suffix {suffix} {'--unblind' if unblind else ''}"
subprocess.run(cmd, shell=True, check=True)

for mass in massPoints:
    cmd = f"python3 doImpacts.py -e {era} -m {mass} -j {settings_file}"
    subprocess.run(cmd, shell=True, check=True)

    cmd = f"python3 doGoodnessOfFit.py -e {era} -m {mass} -j {settings_file} -t 500 -s 123456"
    subprocess.run(cmd, shell=True, check=True)

    cmd = f"python3 doBiasTest.py -e {era} -m {mass} -j {settings_file} -t 500"
    subprocess.run(cmd, shell=True, check=True)