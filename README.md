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

- `-m <letters>`: steps to run (c=collect, s=symmetrize JES/JER, m=fix zero-content bins, d=datacards, l=limits, p=Brazil plot, i=impacts, g=GoF, b=bias). `s` and `m` add `symmetrized`/`zerosFixed` to the suffix, so keep them also when rerunning without collecting (e.g. `-m smdlp`)
- `-s <suffix>`: label the whole run (e.g. `histo2023_<suffix>.root`, `TprimeToTZ_<mass>_<suffix>/`)
- `-u`: unblind (use data instead of the background sum)

A copy of the settings and the list of executed commands (`settings_<suffix>.json`, `commands_<suffix>.sh`) is saved in the `dc-folder`, together with the limits (`Limits_<era>_<suffix>.json`).

## Combining eras

```bash
python3 perform-statistical-analysis.py -e 2023+2024 -s <suffix> -m csmdlp
```

- The histogram steps (c, s, m) are run for each era, in that era's `dc-folder`.
- One datacard per era is written in `<dc-folder of 2023+2024>/TprimeToTZ_<mass>_<suffix>/<era>/`, and the two are merged with `combineCards.py` into `TprimeToTZ_<mass>.txt` (bins prefixed `y<era>_`).
- Systematics with `"correlated": false` in the settings (JES, JER) get one nuisance per era (`jesTotal_2023`, `jesTotal_2024`, ...); all the others stay correlated.
- The luminosity uncertainty follows the correlation scheme of LumiRecommendationsRun3 for the combined years (`lumi-combinations` in the settings): 2022EE counts as 2022 and 2023postBPix as 2023.
- `commands_<suffix>.sh` in the combination `dc-folder` contains all the steps of all eras, to reproduce the result from scratch.

## Single steps

```bash
python3 CollectHistos.py -e 2023 --addSyst                      # collect histograms -> histo2023.root
python3 symmetrizeHistos.py -i <dc-folder>/histo2023.root -s jesTotal,jer   # symmetrize JES/JER
python3 makePositiveHistos.py -i <dc-folder>/histo2023_symmetrized.root     # fix zero-content bins
python3 CreateDatacards.py -e 2023 --addSyst --addMCStat        # write datacards
python3 BrazilPlot.py -e 2023                                   # limits (Brazil plot)
python3 doImpacts.py -e 2023 -m 1000                            # impacts
python3 doGoodnessOfFit.py -e 2023 -m 1000 -t 500               # goodness of fit (+ plot)
python3 doBiasTest.py -e 2023 -m 1000 -t 500                    # bias test
```

To redo only the GoF plot: `python3 plotGoodnessOfFit.py -i <dc-folder>/TprimeToTZ_1000/gof/gof.json -e 2023 -m 1000`.
