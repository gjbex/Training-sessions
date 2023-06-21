#!/usr/bin/env bash

# define demo-magic functions
source ../demo-magic.sh

# ensure clean build and clear the screen
rm -rf build/
clear

# show first version of the code
pe 'cat hello_01.c'

# compile and discuss compilation errors
pe 'gcc  hello_01.c  -o hello.exe'

# show second version of the code
pe 'cat hello_02.c'

# compile to show it was fixed
pe 'gcc  hello_02.c  -o hello.exe'

# run the application, point out the missing new line
pe './hello.exe'

# show the final version of the code
pe 'cat hello_03.c'

# compile to show it was fixed
pe 'gcc  hello_03.c  -o hello.exe'

# run the application, point out the missing new line
pe './hello.exe'

# remove executable
pe 'rm hello.exe'

# show CMake file
pe 'cat CMakeLists.txt'

# create a build directory
pe 'mkdir  -p  build'

# generate build environment
pe 'cmake -B build -S .'

# build the application
pe 'cmake --build build/'

# run the application
pe './build/hello.exe'

# make suse the original prompt doesn't show
# immediately
wait
