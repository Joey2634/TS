#! /bin/bash

dir=/share_data
if [ ! -d $dir ]
then
  sudo mkdir $dir
  echo -e "\033[32m this is $dir success ! \033[0m"
else
  echo -e "\033[032m directory already exists \033[0m"
fi

sudo mount -t nfs 10.24.206.199:/share_data /share_data
