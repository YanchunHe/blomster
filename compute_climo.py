#!/usr/bin/env python

import calendar
import copy
import os
import subprocess

#import sys
from pathlib import Path

from ruamel.yaml import YAML
from pyprojroot import here
# Get project root
root_path = Path(here())

# read recipe.yml
yaml=YAML()
with open(root_path.joinpath('recipe.yml')) as f:
    cfg = yaml.load(f)

    work_root = cfg["blomster"]["work_root"]
    overwrite = cfg["blomster"]["overwrite"]

    caseid = cfg["experiment"]["caseid"]
    input_root = cfg["experiment"]["input_root"]
    year_start = cfg["experiment"]["year_start"]
    year_end = cfg["experiment"]["year_end"]

    variables = cfg["variables"]

# make leading zeros
yyyy1 = f"{year_start:04d}"
yyyy2 = f"{year_end:04d}"
    
# define the frequency mapping for each tag
freq={"hy": "yearly", "hm": "monthly",
      "hbgcy": "yearly", "hbgcm": "monthly",
      "h":"monthly", "h1":"daily"}
realm = {
    "blom": "ocn",
    "cice": "ice",
    "micom": "ocn",
}

# Save generated climatology information to a YAML file
settings_file = "notebooks/settings.yml"
with open(root_path.joinpath(settings_file), "r") as f:
    settings = yaml.load(f)

settings["climos"] = {
    "blom": {
        "hy": {},
        "hm": {},
        "hbgcy": {},
        "hbgcm": {},
    },
    "cice": {
        "h": {},
        "h1": {},
    }
}
settings["timeseries"] = copy.deepcopy(settings["climos"])

# Common configuration based on your ncclimo output
suffix = "climo.nc"

# Define seasons with their respective start and end months (ncclimo standard)
seasons_meta = {
    "ANN": ("01", "12"),
    "DJF": ("01", "12"),  # ncclimo typically sets DJF to the full year span
    "MAM": ("03", "05"),
    "JJA": ("06", "08"),
    "SON": ("09", "11"),
}


# Optional: ensure system NCO is used, not a user-overridden version
env = os.environ.copy()
env['NCO_PATH_OVERRIDE'] = 'No'

for model, tags in variables.items():       # model: [blom, cice]
    for tag, varlist in tags.items():         # tag: [hy, hm, hbgcy, hbgcm]
        climo = varlist["climo"]
        if not climo:
            continue
        print("----------------------------------")
        print(f"Process: {model}, {tag}, {climo}")

        # test model tag, blom or micom
        mdl_nm = model
        if model == 'blom':
            data_path = Path(input_root).joinpath(f"{caseid}/{realm[model]}/hist")
            file_pattern = f"{caseid}.blom.{tag}_{yyyy1}*.nc"
            if not any(data_path.glob(file_pattern)):
                file_pattern = f"{caseid}.micom.{tag}_{yyyy1}*.nc"
                mdl_nm = 'micom'
        # ncclimo arguments
        args = [
            "nco/ncclimo",
            "-m", mdl_nm,
            "-h", tag,
            f"--clm_md={freq[tag]}",
            "-c", cfg['experiment']['caseid'],
            "-i", f"{input_root}/{caseid}/{realm[model]}/hist",
            "-o", f"{work_root}/{caseid}/{model}.{tag}",
            "-s", str(year_start),
            "-e", str(year_end),
            "-v", ",".join(climo),
            "-p", "background",
            "-j", "6"              
        ]

        if overwrite is True:
            # Execute ncclimo
            print(" ".join(args))
            process = subprocess.run(
                args,
                check=False,
               #capture_output=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True
            )
            # Check for success
            if process.returncode == 0:
                print("Climatology generated successfully.")
            else:
                print("\nERROR: Climatology generation failed.")
                print(process.stdout)
        else:
            print("Skip computing existing climotologies..")

        # Monthly files (01 to 12)
        for i in range(1, 13):
            mm = f"{i:02d}"
            mth = calendar.month_abbr[i].upper()
            fname = f"{caseid}_{mm}_{yyyy1}{mm}_{yyyy2}{mm}_{suffix}"
            settings['climos'][model][tag][mth] = f"{work_root}/{caseid}/{model}.{tag}/{fname}"
        
        # Seasonal files
        for climo_period, (start_m, end_m) in seasons_meta.items():
            fname = f"{caseid}_{climo_period}_{yyyy1}{start_m}_{yyyy2}{end_m}_{suffix}"
            settings['climos'][model][tag][climo_period] = f"{work_root}/{caseid}/{model}.{tag}/{fname}"

        # ANN files
        start_m, end_m = seasons_meta["ANN"]
        fname = f"{caseid}_ANN_{yyyy1}{start_m}_{yyyy2}{end_m}_{suffix}"
        settings['climos'][model][tag]['ANN'] = f"{work_root}/{caseid}/{model}.{tag}/{fname}"

# Write the structure to a YAML file
with open(root_path.joinpath(settings_file), "w") as f:
    yaml.dump(settings, f)
