# Training sessions

This is a (non-exhaustive) list of trainings offered on a regular basis
by the VSC, but also to research institutes and companies.

All of these trainings can be tailored to the audience if required,
and ad-hoc trainings are possible as well.

For many sessions, a dedicated website has been created that provides
detailed information, as well as a link to a GitHub repository that
hosts the material specific for that training.

For those sessions that do not yet have their own dedicated website,
the material can be found in the training-masterials repository:
[https://github.com/gjbex/training-material](https://github.com/gjbex/training-material)

## C++ for scientific programming (14 hours)

This training focusses on using C++ for scientific programming and on
the way Bjarne Stroustrup advocates modern C++ in his book "A tour of
C++".  Some C++17 features and third party libraries will also be
discussed.

Subjects:

  * basics: control flow statements, data types, functions
  * user defined types: structs, classes
  * modularization of code
  * error handling
  * classes: inheritance 
  * templates
  * strings and regular expressions
  * I/O streams
  * STL containers and algorithms
  * numerics, Armadillo for linear algebra, GNU Scientific Library

Prerequisites:

  * experience in another programming language


## Fortran (7 hours)

Fortran is used a lot in the context of HPC.  For many, it has a
reputation of being an old and ugly programming language.  However,
modern Fortran is a far cry from Fortran 77 that its detractors have
in mind.  Fortran 2003/2008 is a language that is well tailored
towards scientific computing.  This training introduces the language
and its features.

For detailed information, see:
[https://github.com/gjbex/Fortran-for-programmers](https://github.com/gjbex/Fortran-for-programmers)


## Python training sessions

### Python as a second language (4 hours)

Python is an all-round programming language that has applications in
many domains.  This training session introduces the programming
language to participants who have programming experience with other
programming languages such as R, MATLAB, C/C++ or Fortran.

Subjects:

  * control flow statements (conditional, repetition)
  * functions
  * data types
  * file I/O

Prerequisites:

  * experience in another programming language


### Python systems programming (4 hours)

Python is a very versatile programming language that has a wide range of
applications.  This training concentrates on interaction with the
operating system, the file system, other applications and the network.
This is useful for systems programming, but also when you want to use
Python as a coordination language for your workflows.

Subjects and Python modules that will be covered:

  * interacting with the operating system: os, platform, sys, psutil
  * interacting with the filesystem: os.path, pathlib, shutil,
    fileinput, tempfile
  * command line arguments & configuration files: argparse, click, configparser 
  * compressing & decompressing files: e.g., gzip, tarfile
  * running & communicating with other processes: sh, subprocess
  * running remote commands using SSH: paramiko
  * logging information, warnings and errors: logging

Prerequisites:

  * experience in Python programming


### Python software engineering (4 hours)

Quality of software matters, whether you share it with others or not.
Software should be easy to install, easy to use, and well documented.
This training will cover those aspects from the perspective of the
Python ecosystem.  However, it is also important that software is easy
to maintain, so coding style matters, API-level documentation should be
available, as well as a battery of tests to ensure the software's
integrity.  Of course, good design is at least as important.

Subjects and Python modules that will be covered:

  * code style and best practices, idiomatic Python: flake8, pylint
  * documentation: docstring, mkdocs
  * user interface: argparse, configparser
  * exception handling
  * type hints and type checking using mypy
  * unit testing: pytest
  * object oriented programming in Python
  * design patterns

Prerequisites:

  * experience in Python programming


### Scientific Python (4 hours)

Python is a nice programming language for scientific programming. Many
high quality libraries are available as building block in a wide variety 
of scientific domains. In this training we will concentrate on the core
libraries, and give some examples of domain specific libraries.

For detailed information, see:
[https://github.com/gjbex/Scientific-Python](https://github.com/gjbex/Scientific-Python)


### Python for data science (4 hours)

Python is one of the dominant languages in data science.  In this
training we will cover a number of modules that are useful for data
preparation, analyzing data, visualization, and machine learning.

For detailed information, see:
[https://github.com/gjbex/Python-for-data-science](https://github.com/gjbex/Python-for-data-science)


### Python for machine learning (4 hours)

Python is one of the dominant languages in the area of machine learning
and AI.  This training will provide an introduction to machine learning
methodology for data preparation and machine learning, as well as some
machine learning algorithms.

subjects and Python modules that will be covered:

  * what is machine learning, and what is AI?
  * pipelines for data ingestion, training and testing: scikit-learn
  * examples of classic algorithms: scikit-learn
    * principal component analysis
    * Ridge regression
    * Naive Bayes classifier
    * k-means clustering
  * examples of (deep) neural networks: Keras
    * multi-layer perceptron for image classification
    * convolutional neural network for image classification
    * recurrent neural networks for sentiment analysis

Prerequisites:

  * experience in Python programming, visualization


### Python for HPC (4 hours)

Although vanilla Python is fairly slow and hence not a good candidate,
there are several options to significantly increase the efficiency of
Python programs.

  * profiling Python code
  * using the numba JIT compiler
  * Cython to generate C code from annotated Python
  * implementing libraries in C, C++ and Fortran
  * concurrency via multiprocessing or concurrent.futures
  * parallelization using dask
  * distributed programming with mpi4py
  * data processing with pyspark

Prerequisites:

  * experience in Python programming
  * for some subjects, experience in programming C, C++ or Fortran


## Jupyter notebooks (2 hours)

Jupyter notebooks are a versatile tools for data exploration and
exploratory programming in a wide variety of programming languages. In this
session you will learn how to use Jupyter Notebooks effectively.

Subjects:

  * formatted text using MarkDown and LaTeX formulas
  * using Python/R code cells
  * mixing Python and R in a single notebook
  * interactive visualizations in notebooks
  * interactive data in notebooks
  * turning notebooks into slides
  * batch execution of notebooks
  * notebooks and version control

Prerequisites:

  * Familiarity with Python or R (note that most examples will be given in Python)


## Parallel programming

These courses have been developed by Rolf Rabenseifner (HLRS, Stuttgart,
Germany) and the training has followed Rolf's train-the-trainer program.

### MPI: Message Passing Interface (14 hours)

MPI is the de-facto standard for distributed parallel programming of
scientific applications.  It specifies language bindings for C and
Fortran.  This training covers the MPI 3.1 standard, but also
emphasizes potential pitfalls and best practices.

Subjects:

  * process model and language bindings
  * messages and point-to-point communication
  * non-blocking communication
  * collective communication
  * groups, communicators and virtual topologies
  * one-sided communication
  * shared memory
  * derived data types
  * parallel I/O
  * best practices

Prerequisites:

  * experience in C, C++ or Fortran programming


### OpenMP (7 hours)

OpenMP provides a very convenient programming model for scientific
applications that run multiple threads.  It is supported by C, C++ and
Fortran compilers.  Its main advantage is that it is mostly used through
annotation of code, which makes it easy to pick low hanging fruit when
starting to parallelize code. The training covers OpenMP 4.5, and
emphasizes pitfalls and best practices.

Subjects:

  * programming and execution model
  * worksharing directives
  * data environment
  * tasking
  * SIMD constructs
  * thread placement
  * pitfalls and best practices

Prerequisites:

  * experience in C, C++ or Fortran programming


### Threading Building Blocks (4 hours)

Threading Building Blocks (TBB) is a C++ template library for developing
shared memory applications.  It integrates well with the C++ Standard
Template Library (STL) and can be used with any modern C++ compiler.
TBB is especially suited for nested parallelism, and pipelining when
part of the application can use accelerator hardware.

Subjects:

  * programming and execution model
  * recap of required C++ features
  * algorithms: `parallel_for`, `parallel_reduce`, `parallel_do`
  * task based programming
  * dataflow programming, task graphs
  * pitfalls and best practices

Prerequisites:

  * experience in C++ programming


## Defensive programming and debugging (4 hours + 2 hours optional)

All code contains bugs, finding and fixing them is boring.  In this
training, best practices are presented to reduce the number of bugs
in your code.  You will also learn about debuggers and debugging
techniques to find bugs more efficiently.

Subjects:

  * best practices in coding, code style, error handling
  * using compiler options to warn about potential issues
  * unit and functional testing
  * using a debugger (breakpoints, inspection, watchpoints, tracing, ...)
  * zoo of bugs
  * optional: debugging parallel code

Prerequisites:

  * experience programming C, C++, or Fortran 
  * familiarity with the bash command line
  * optional: experience using MPI and/or OpenMP


## Optimization (4 hours)

For HPC applications, performance is a major concern.  A thorough
understanding of the relevant hardware and software components is
required.  In this training, you will learn about a number of these
components, and how they influence the efficiency of you application.
You will also learn how to profile your application to identify
performance bottlenecks.

Subjects:

  * parallel efficiency 
  * memory: cache hierarchy, cache lines, memory access patterns,
    cache associativity
  * CPU: vectorization
  * pitfalls, e.g., double promotion, false sharing
  * feedback guided optimization
  * performance measures
  * profiling

Prerequisites:

  * experience programming C, C++, or Fortran 
  * experience using MPI and/or OpenMP
  * familiarity with the bash command line


## Linux bash shell (4 hours)

In HPC, most interaction with the systems is through the terminal and
a shell.  Working efficiently in such an environment saves a lot of time
and frustration.  In this training, you will learn the basics of bash,
as well as some Linux OS concepts.

Subjects:

  * interacting with files and directories
  * editors: nano, and hints at more sophisticated editors
  * process management
  * sharing: file and directory permissions
  * searching: find and grep
  * compressed files and archives: tar, gzip
  * copying to/from remote systems: scp, sftp, rclone

Prerequisites:

  * none


## Container for HPC (3 hours)

Singularity can be viewed as the Docker for HPC, i.e., a Singularity
image contains all the operating system/software components for your
application and can be deployed and run on HPC infrastructure, as well
as on your own laptop.

For detailed information, see:
[https://github.com/gjbex/Containers-for-HPC](https://github.com/gjbex/Containers-for-HPC)


## Version control: git or SVN (3 hours)

Version control is an essential part of the software development process
and is crucial for scientific application to help reproducibility.
You will learn how to use a version control system (either git or SVN)
to document the changes in your source code.

For detailed information, see:
[https://github.com/gjbex/Version-control-with-git](https://github.com/gjbex/Version-control-with-git)
