# TprimeStats

Statistical analysis (datacards, limits, impacts, GoF, bias test) for the T' → tZ search, based on combine.

## Environment setup (once)

```bash
cmsrel CMSSW_16_0_0
cd CMSSW_16_0_0/src
cmsenv
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
git -C HiggsAnalysis/CombinedLimit checkout v11.1.0
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
git -C CombineHarvester checkout v4.0.0
scram b -j 8
# cmsstyle (used by the plotting scripts) goes into the release's virtual env
scram-venv
cmsenv
PYTHONNOUSERSITE=1 python3 -m pip install cmsstyle
```

Documentation:
- combine v11 --> https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/#within-cmssw-recommended-for-cms-users
- combine harvester --> https://cms-analysis.github.io/CombineHarvester/

To check the installed versions: `git -C HiggsAnalysis/CombinedLimit describe --tags` (same for `CombineHarvester`).

## Environment in every session: `tprime-limit.sh`

Create `~/tprime-limit.sh`:

```bash
#!/bin/bash
cd ~/CMSSW_16_0_0/src
cmsenv
# Keep user packages (notably NumPy 2.x) from overriding CMSSW dependencies.
# cmsstyle is installed in this release's scram-venv.
export PYTHONNOUSERSITE=1
cd ~/TprimeStats
```

and load it with:

```bash
source ~/tprime-limit.sh
```

Use `source`, not `bash` or `./`: otherwise the `cmsenv` environment is lost when the script ends.

## Configuration

Everything is driven by `settings.json`: input plots folder and output datacard folder per era (`plots-folder`, `dc-folder`), `processes` (backgrounds and signals), `samples`, `categories` and `systematics`.

Luminosity:
- integrated luminosity per era (`lumi_dict`): [PdmVRun3Analysis](https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmVRun3Analysis)
- luminosity uncertainty (`systematics.lumi`, `lumi-combinations`): [LumiRecommendationsRun3](https://twiki.cern.ch/twiki/bin/view/CMS/LumiRecommendationsRun3)

## Full analysis

```bash
python3 perform-statistical-analysis.py -e 2023 -m csmdlp
```

- `-m <letters>`: steps to run (c=collect, s=symmetrize JES/JER, m=fix zero-content bins, d=datacards, l=limits, p=Brazil plot, i=impacts, g=GoF, b=bias), default all (`csmdlpbig`). `s` and `m` add `symmetrized`/`zerosFixed` to the suffix, so keep them also when rerunning without collecting (e.g. `-m smdlp`)
- `-s <suffix>`: label the whole run (e.g. `histo2023_<suffix>.root`, `TprimeToTZ_<mass>_<suffix>/`)
- `-u`: unblind (use data instead of the background sum)
- `--testMasses <masses>`: comma-separated masses in GeV (e.g. `1000`) for impacts, GoF and bias; default all masses
- `-v <variant>`: extra label for a datacard-level variation (`TprimeToTZ_<mass>_<suffix>_<variant>/`)
- `--dryrun`: only write `commands_<suffix>.sh`, without running it

The zero fix (`m`) sets the MC bins below 1e-8 (zero or negative, e.g. from negative weights) to 1e-6. `data_obs` is never changed, except for the negative bins of the blinded pseudo-data (sum of backgrounds), which are set to 0.

A copy of the settings and the list of executed commands (`settings_<suffix>.json`, `commands_<suffix>.sh`) is saved in the `dc-folder`, together with the limits (`Limits_<era>_<suffix>.json`).

The impacts (`i`) are done on the Asimov dataset twice, background only and with r = median expected limit of that mass (`-t -1 --expectSignal 0/<r exp.>`, read from the `out.log` of the limits), in `TprimeToTZ_<mass>_<suffix>/impacts_r0/` and `impacts_rexpected/`.

If a step fails (e.g. the impacts), the next steps are still run, but the script exits with an error at the end.

## Combining eras

```bash
python3 perform-statistical-analysis.py -e 2023+2024 -s <suffix> -m csmdlp
```

- The histogram steps (c, s, m) are run for each era, in that era's `dc-folder`.
- One datacard per era is written in `<dc-folder of 2023+2024>/TprimeToTZ_<mass>_<suffix>/<era>/`, and the two are merged with `combineCards.py` into `TprimeToTZ_<mass>.txt` (bins prefixed `y<era>_`).
- Systematics with `"correlated": false` in the settings (JES, JER) get one nuisance per era (`jesTotal_2023`, `jesTotal_2024`, ...); all the others stay correlated.
- The luminosity uncertainty follows the correlation scheme of LumiRecommendationsRun3 for the combined years (`lumi-combinations` in the settings): 2022EE counts as 2022 and 2023postBPix as 2023.
- `commands_<suffix>.sh` in the combination `dc-folder` contains all the steps of all eras, to reproduce the result from scratch.

## Running on HTCondor

Long runs survive the logout from lxplus only on batch. One job per settings file; the eras run in sequence inside the job, each one with all its steps. The options the submitter doesn't know (`-m`, `-s`, `-u`, `--testMasses`, ...) go to `perform-statistical-analysis.py`:

```bash
python3 condor_submitter.py -j settingsA.json settingsB.json -e 2023+2024 2023 2024 -m csmdlpig --testMasses 1000
python3 condor_submitter.py --status                 # all jobs in condor/, or give the job folders
python3 condor_submitter.py --resubmit condor/<launchtime>_*   # failed/removed jobs among these, only the eras not DONE
```

- `--flavour` (default `tomorrow` = 1 day), `--cpus` (default 8), `--cmssw` (default `~/CMSSW_16_0_0/src`), `--dryrun` (write the job files, or show what would be resubmitted, without submitting)
- job files and logs in `condor/<launchtime>_<settings>/`, with a copy of the settings (the batch nodes don't see local `/tmp`) and `job.json` (eras and options, used by `--status` and `--resubmit`)
- a failed era doesn't stop the next ones: each era leaves `DONE_<era>` or `FAILED_<era>` in the job folder, and the job exits with an error if any era failed

## Single steps

```bash
python3 CollectHistos.py -e 2023 --addSyst                      # collect histograms -> histo2023.root
python3 symmetrizeHistos.py -i <dc-folder>/histo2023.root -s jesTotal,jer   # symmetrize JES/JER
python3 makePositiveHistos.py -i <dc-folder>/histo2023_symmetrized.root     # fix zero-content bins
python3 CreateDatacards.py -e 2023 --addSyst --addMCStat        # write datacards
python3 RunLimits.py -e 2023                                    # limits, 8 masses in parallel (--jobs) -> Limits_2023.json
python3 BrazilPlot.py -e 2023                                   # limits (Brazil plot)
python3 CompareLimits.py -i <dc-folder A>/Limits_2024_<suffix>.json <dc-folder B>/Limits_2024_<suffix>.json -l "A" "B" -o CompareLimits   # median expected limits of several runs vs Full Run 2 expected and theory
python3 doImpacts.py -e 2023 -m 1000 --outdir impacts_rexpected --expectSignal expected   # impacts on Asimov (-t -1), --expectSignal 0, 1, ... or expected (median expected limit)
python3 doGoodnessOfFit.py -e 2023 -m 1000 -t 500               # goodness of fit (+ plot)
python3 doBiasTest.py -e 2023 -m 1000 -t 500                    # bias test (--robustFit 1), injected r x toy chunks in parallel (--jobs 8, --split 5)
```

To redo only the GoF plot: `python3 plotGoodnessOfFit.py -i <dc-folder>/TprimeToTZ_1000/gof/gof.json -e 2023 -m 1000`.
