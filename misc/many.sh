#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_PATH="${REPO_ROOT}/src/config.py"

DIRS="2015010100 2015012500 2015022200 2015032500 2015042400 2015052500 2015062400 2015072500 2015082500 2015092400 2015102500 2015112400"
for i in $DIRS 
do
   sed -i -- 's/aaa/'$i'/g' "${CONFIG_PATH}"
   sed -i -- 's/bbb/'$i'/g' "${CONFIG_PATH}"
   head -n 3 "${CONFIG_PATH}"
   #ACTION
   python "${REPO_ROOT}/main.py"

   sed -i -- 's/'$i'/aaa/g' "${CONFIG_PATH}"
   sed -i -- 's/'$i'/bbb/g' "${CONFIG_PATH}"
   echo $i DONE!
   #sleep 1000
   echo " "
   find "${REPO_ROOT}" -name '*.pyc' -delete
done
