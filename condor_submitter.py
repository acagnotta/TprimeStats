import argparse
import glob
import json
import os
import shlex
import shutil
import subprocess
import time

usage = """python3 condor_submitter.py -j settingsA.json [settingsB.json ...] -e 2023+2024 2023 2024 [--dryrun] <options of perform-statistical-analysis.py>
       python3 condor_submitter.py --status   [condor/<job folder> ...]
       python3 condor_submitter.py --resubmit [condor/<job folder> ...]"""
# allow_abbrev=False: an option of perform-statistical-analysis.py is never taken as a short form of one of the submitter
parser = argparse.ArgumentParser(description="Run perform-statistical-analysis.py on HTCondor: one job per settings file, the eras run in sequence inside the job", usage=usage, allow_abbrev=False)
parser.add_argument('-j', '--jsonInput',    type=str,   nargs='+',  default=[],             help='Settings JSON file(s), one job each')
parser.add_argument('-e', '--eras',         type=str,   nargs='+',  default=['2024'],       help='Eras to run in sequence (e.g. 2023+2024 2023 2024)')
parser.add_argument('--flavour',            type=str,               default='tomorrow',     help='JobFlavour: espresso=20min, microcentury=1h, longlunch=2h, workday=8h, tomorrow=1d, testmatch=3d, nextweek=1w')
parser.add_argument('--cpus',               type=int,               default=8,              help='request_cpus')
parser.add_argument('--cmssw',              type=str,               default=os.path.expanduser('~/CMSSW_16_0_0/src'), help='CMSSW src folder with combine')
parser.add_argument('--dryrun',             action='store_true',                            help='Write the job files without submitting')
parser.add_argument('--status',             type=str,   nargs='*',  default=None,           help='Print the status of these job folders (default: all in condor/)')
parser.add_argument('--resubmit',           type=str,   nargs='*',  default=None,           help='Resubmit the failed jobs of these job folders (default: all in condor/), only the eras not DONE')
# the options not known here (e.g. -m, -s, -u, --testMasses) go untouched to perform-statistical-analysis.py
args, pas_options = parser.parse_known_args()

repo_folder     = os.path.dirname(os.path.abspath(__file__))
condor_folder   = f"{repo_folder}/condor"


def runner_writer(job_folder, job):
    with open(f"{job_folder}/runner.sh", "w") as f:
        f.write("#!/bin/bash\n")
        # same environment as tprime-limit.sh, without the cmsenv alias that batch shells don't have
        f.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n")
        f.write(f"cd {job['cmssw']} && eval $(scramv1 runtime -sh)\n")
        f.write("export PYTHONNOUSERSITE=1\n")
        f.write(f"cd {repo_folder}\n")
        f.write("rc=0\n")
        # a failed era doesn't stop the next ones: it leaves FAILED_<era> and the job exits with 1 at the end
        for era in job["eras"]:
            f.write(f"echo '=== {era}'\n")
            f.write(f"if python3 perform-statistical-analysis.py -j {job['settings']} -e {era} {shlex.join(job['options'])}; then\n")
            f.write(f"    touch {job_folder}/DONE_{era}; echo '=== DONE {era}'\n")
            f.write("else\n")
            f.write(f"    touch {job_folder}/FAILED_{era}; echo '=== FAILED {era}'; rc=1\n")
            f.write("fi\n")
        f.write("exit $rc\n")
    os.chmod(f"{job_folder}/runner.sh", 0o755)

def sub_writer(job_folder, job):
    label = job["label"]
    with open(f"{job_folder}/condor.sub", "w") as f:
        f.write("universe                = vanilla\n")
        f.write(f"+JobFlavour             = \"{job['flavour']}\"\n")
        f.write(f"+JobTag                 = \"stats_{label}\"\n")
        f.write(f"request_cpus            = {job['cpus']}\n")
        f.write(f"executable              = {job_folder}/runner.sh\n")
        f.write(f"output                  = {job_folder}/output/{label}.out\n")
        f.write(f"error                   = {job_folder}/error/{label}.err\n")
        f.write(f"log                     = {job_folder}/log/{label}.log\n")
        f.write("queue\n")

def submit(job_folder):
    if args.dryrun:
        print(f"    dryrun: condor_submit {job_folder}/condor.sub")
        return
    subprocess.run(f"condor_submit {job_folder}/condor.sub", shell=True, check=True)

def condor_state(job_folder, job):
    # last meaningful event of the condor log: 000 submitted, 001 executing, 004 evicted, 005 terminated, 009 aborted, 012 held, 013 released
    states  = {"000": "idle", "001": "running", "004": "idle", "009": "removed", "012": "held", "013": "idle"}
    state, cluster = "not submitted", ""
    log = f"{job_folder}/log/{job['label']}.log"
    if not os.path.exists(log):
        return state, cluster
    for line in open(log):
        code = line[:3]
        if code == "000":
            cluster = line.split()[1].strip("()").split(".")[0]
        if code in states:
            state = states[code]
        elif code == "005":
            state = "terminated"
        elif "return value" in line:
            state = "done" if line.split("return value")[1].strip(" )\n") == "0" else "failed"
    return state, cluster

def job_folders(selected):
    return [f.rstrip("/") for f in selected] if selected else sorted(os.path.dirname(f) for f in glob.glob(f"{condor_folder}/*/job.json"))

def eras_with(job_folder, job, tag):
    return [era for era in job["eras"] if os.path.exists(f"{job_folder}/{tag}_{era}")]


if args.status is not None:
    for job_folder in job_folders(args.status):
        job             = json.load(open(f"{job_folder}/job.json"))
        state, cluster  = condor_state(job_folder, job)
        done, failed    = eras_with(job_folder, job, "DONE"), eras_with(job_folder, job, "FAILED")
        todo            = [era for era in job["eras"] if era not in done + failed]
        print(f"{os.path.basename(job_folder)}: {state} {cluster}")
        print(f"    done: {' '.join(done) or '-'}   failed: {' '.join(failed) or '-'}   to do: {' '.join(todo) or '-'}")

elif args.resubmit is not None:
    for job_folder in job_folders(args.resubmit):
        job             = json.load(open(f"{job_folder}/job.json"))
        state, cluster  = condor_state(job_folder, job)
        if state not in ["failed", "removed"]:
            if state == "held": print(f"{os.path.basename(job_folder)}: held, check with condor_q -hold {cluster}")
            continue
        job["eras"]     = [era for era in job["eras"] if era not in eras_with(job_folder, job, "DONE")]
        print(f"{os.path.basename(job_folder)}: {state} {cluster}, resubmitting eras {' '.join(job['eras'])}")
        if args.dryrun: continue
        # keep the output of the previous attempt, the condor log just goes on
        for sub, ext in [("output", "out"), ("error", "err")]:
            old = f"{job_folder}/{sub}/{job['label']}.{ext}"
            if os.path.exists(old): os.rename(old, f"{old}.{time.strftime('%Y%m%d_%H%M%S')}")
        for era in job["eras"]:
            if os.path.exists(f"{job_folder}/FAILED_{era}"): os.remove(f"{job_folder}/FAILED_{era}")
        runner_writer(job_folder, job)
        submit(job_folder)

else:
    if not args.jsonInput: parser.error("-j is needed to submit")
    launchtime = time.strftime("%Y%m%d_%H%M%S")
    for settings in args.jsonInput:
        label       = os.path.splitext(os.path.basename(settings))[0]
        job_folder  = f"{condor_folder}/{launchtime}_{label}"
        for sub in ["output", "error", "log"]:
            os.makedirs(f"{job_folder}/{sub}", exist_ok=True)
        # copy of the settings next to the job, the batch nodes don't see local /tmp folders
        shutil.copy(settings, job_folder)
        job = {"label": label, "settings": f"{job_folder}/{os.path.basename(settings)}", "eras": args.eras, "options": pas_options,
               "flavour": args.flavour, "cpus": args.cpus, "cmssw": args.cmssw}
        with open(f"{job_folder}/job.json", "w") as f:
            json.dump(job, f, indent=2)
        runner_writer(job_folder, job)
        sub_writer(job_folder, job)
        print(f"{label}: {job_folder} (eras {' '.join(args.eras)}, options {shlex.join(pas_options)})")
        submit(job_folder)
