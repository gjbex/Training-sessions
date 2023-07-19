#!/usr/bin/env bash

# define everthing required for demo-magic
. demo-magic.sh

# prepare the screen by clearning it
clear

# press enter for the command to appear, press enter to execute
pe 'ls -l'

# press enter for the command to appear, press enter to execute
pe 'cat simple.sh'

# wait so that the script doesn't exit immediately
wait
