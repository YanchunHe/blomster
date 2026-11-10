#!/usr/bin/env -S -i bash
set -e

user=$(whoami)

# activate conda
for conda_sh in \
  "/conda/miniconda3/etc/profile.d/conda.sh" \
  "/cluster/software/Miniforge3/24.1.2-0/etc/profile.d/conda.sh"
do
  if [ -f "${conda_sh}" ]; then
    . "${conda_sh}"
    break
  fi
done
conda activate /nird/datalake/NS16000B/blomster-env

# parse experiment info
caseid=$(yq -r '.experiment.caseid' recipe.yml)
year_start=$(yq -r '.experiment.year_start' recipe.yml)
year_end=$(yq -r '.experiment.year_end' recipe.yml)
www_root=$(yq -r '.jupyterbook.www_root' recipe.yml)
work_root=$(yq -r '.workdir.work_root' recipe.yml)
project=$(echo $www_root |grep -oP 'NS\d+K' |tr '[:upper:]' '[:lower:]')
if echo $www_root | grep 'datalake' >/dev/null 2>&1 ; then
  dataservice='datalake'
else
  dataservice='datapeak'
fi

# set permission
umask 002

# generate TOC and inject parameters to notebooks
python configure.py
python compute_climo.py

# build the book
jupyter-book clean notebooks --all
jupyter-book build -qq -n notebooks

# Backup configs 
cp recipe.yml notebooks/{_config.yml,_toc.yml,settings.yml} notebooks/_build/jupyter_execute/

# Publish
chmod -R g+w notebooks/_build/html
if test -w ${www_root} ; then
  www_sub=${caseid}/yrs${year_start}to${year_end}-obs
  mkdir -p ${www_root}/${www_sub}
  rsync -au --delete --remove-source-files notebooks/_build/html/ ${www_root}/${www_sub}
  echo 'Gedneratd diagnostics is at:'
  echo "https://${project}.web.sigma2.no/${dataservice}/diagnostics/blomster/$user/${www_sub}"
else
  echo "You do not have write permission to ${www_root}."
  echo "Generated diagnostics is under:"
  echo "notebooks/_build/html"
fi

# cleanup
#for nbdir in $(cat recipe.yml|grep '\- file: ' |cut -d: -f2 |awk -F/ '{print $(NF-1)}' |uniq)
##for nbdir in $(yq -r '.diagnostics.root' recipe.yml) $(yq -r '.diagnostics.chapters' recipe.yml|grep 'file' |cut -d: -f2 |awk -F/ '{print $(NF-1)}' |uniq)
#do
#  echo $nbdir
#  rm -rf $nbdir
#done
