#!/bin/bash
# Median expected limits of several region combinations vs Full Run 2 expected and theory (CompareLimits.py)
# To add a combination: one more line in "inputs" and one in "labels", in the same order

S=/eos/user/l/lfavilla/RDF_DManalysis/stats/2024
suffix=symmetrized_zerosFixed

inputs=(
    $S/6SR_blinded/Limits_2024_$suffix.json
    $S/3SR_blinded/Limits_2024_$suffix.json
    $S/6SR_3LooseCR_blinded/Limits_2024_$suffix.json
    $S/3SR_3LooseCR_blinded/Limits_2024_$suffix.json
)
labels=(
    "6 SR"
    "3 SR (no fwd-jet split)"
    "6 SR + 3 Loose CR"
    "3 SR + 3 Loose CR"
)

python3 CompareLimits.py -i "${inputs[@]}" -l "${labels[@]}" -o $S/CompareLimits_2024
