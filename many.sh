#!/bin/bash

DIRS="2015010100 2015012500 2015022200 2015032500 2015042400 2015052500 2015062400 2015072500 2015082500 2015092400 2015102500 2015112400"
for i in $DIRS 
do
   sed -i -- 's/aaa/'$i'/g' ./config.py
   sed -i -- 's/bbb/'$i'/g' ./config.py
   head -n 3 ./config.py
   #ACTION
   python ./main.py

   sed -i -- 's/'$i'/aaa/g' ./config.py
   sed -i -- 's/'$i'/bbb/g' ./config.py
   echo $i DONE!
   #sleep 1000
   echo " "
   rm *.pyc
done