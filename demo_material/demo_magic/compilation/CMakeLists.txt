cmake_minimum_required(VERSION 3.0)
project(hello_world LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED YES)
set(CMAKE_C_EXTENSIONS NO)

add_executable(hello.exe hello_03.c)
