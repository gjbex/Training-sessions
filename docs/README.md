# Training sessions

This is a (non-exhaustive) list of training sessions offered on a regular basis
by the VSC, but also to research institutes and companies.

All of these training sessions can be tailored to the audience if required,
and ad-hoc training sessions are possible as well.

For many sessions, a dedicated website has been created that provides
detailed information, as well as a link to a GitHub repository that
hosts the material specific for that training.

For those sessions that do not yet have their own dedicated website,
the material can be found in the training-masterials repository:
[https://github.com/gjbex/training-material](https://github.com/gjbex/training-material)

## C++ for scientific programming (14 hours)

This training focuses on using C++ for scientific programming and on
the way Bjarne Stroustrup advocates modern C++ in his book "A tour of
C++".  Some C++17 features and third party libraries will also be
discussed.

For detailed information, see:
[https://gjbex.github.io/Scientific-C-plus-plus/](https://gjbex.github.io/Scientific-C-plus-plus/)


## Fortran for programmers (8 hours)

Fortran is used a lot in the context of HPC.  For many, it has a
reputation of being an old and ugly programming language.  However,
modern Fortran is a far cry from Fortran 77 that its detractors have
in mind.  Fortran 2003/2008 is a language that is well tailored
towards scientific computing.  This training introduces the language
and its features.

For detailed information, see:
[https://gjbex.github.io/Fortran-for-programmers/](https://gjbex.github.io/Fortran-for-programmers/)


## C for programmers (12 hours)

C is still one of the more popular programming languages today.  It is
probably mainly used for systems programming, but there are also many
applications for scientific computing that have been developed in this
programming language.

Subject:

  * data types and operators
  * control flow statements
  * functions
  * pointers
  * arrays
  * structures
  * I/O and command line arguments
  * C99 extensions
  * using third party libraries, e.g., GSL

Prerequisites:

  * experience in another programming language


## Python training sessions

### Python for programmers (4 hours)

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
This training introduces modules that are useful in that context.

For detailed information, see:
[https://gjbex.github.io/Python-for-systems-programming/](https://gjbex.github.io/Python-for-systems-programming/)


### Python software engineering (4 hours)

Quality of software matters, whether you share it with others or not.
Software should be easy to install, easy to use, and well documented.
This training will cover those aspects from the perspective of the
Python ecosystem.  However, it is also important that software is easy
to maintain, so coding style matters, API-level documentation should be
available, as well as a battery of tests to ensure the software's
integrity.  Of course, good design is at least as important.

For detailed information, see:
[https://gjbex.github.io/Python-software-engineering/](https://gjbex.github.io/Python-software-engineering/)


### Scientific Python (4 hours)

Python is a nice programming language for scientific programming. Many
high quality libraries are available as building block in a wide variety
of scientific domains. In this training we will concentrate on the core
libraries, and give some examples of domain specific libraries.

For detailed information, see:
[https://gjbex.github.io/Scientific-Python/](https://gjbex.github.io/Scientific-Python/)


### Python for data science (4 hours)

Python is one of the dominant languages in data science.  In this
training we will cover a number of modules that are useful for data
preparation, analyzing data, visualization, and machine learning.

For detailed information, see:
[https://gjbex.github.io/Python-for-data-science/](https://gjbex.github.io/Python-for-data-science/)


### Python for machine learning (4 hours)

Python is one of the dominant languages in the area of machine learning
and AI.  This training will provide an introduction to machine learning
methodology for data preparation and machine learning, as well as some
machine learning algorithms.

For detailed information, see:
[https://gjbex.github.io/Python-for-machine-learning/](https://gjbex.github.io/Python-for-machine-learning/)


### Python for HPC (8 hours)

Although vanilla Python is fairly slow and hence not a good candidate,
there are several options to significantly increase the efficiency of
Python programs.

For detailed information, see:
[https://gjbex.github.io/Python-for-HPC/](https://gjbex.github.io/Python-for-HPC/)


### Python on GPUs (4 hours)

Python is more and more used for scientific computing and can be used
to develop code that runs on GPGPUs.  Additionally, a number of libraries
that are commonly used in scientific computing, data science and machine
learning can use GPGPUs to improve performance.

For detailed information, see:
[https://gjbex.github.io/Python-on-GPUs/](https://gjbex.github.io/Python-on-GPUs/)


### Python dashboards

Dashboards are a useful way to present data in an interactive way.  They can be used
for reporting, but also for data exploration, or even to create simple web applications.
You can run dashboards locally, or deploy them via GitHub or GitLab, or even on a
server in the cloud.  Creating dashboards in Python is quite straightforward.  In this
training you will learn about several frameworks and their strenghts and weaknesses.

For detailed information, see:
[https://gjbex.github.io/Python-dashboards/](https://gjbex.github.io/Python-dashboards/)


## Julia: the good, the bad and the ugly (4 hours)

Julia has gained quite some traction over the last couple of years, but is it for you?
In this training you will see how it compares to MATLAB and Python, and what Julia's
strong and weak points are.

For detailed information, see:
[https://gjbex.github.io/Julia_good_bad_ugly/](https://gjbex.github.io/Julia_good_bad_ugly/)


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

### Parallel programming with MPI (14 hours)

MPI (Message Passing Interface) is the de-facto standard for distributed
parallel programming of scientific applications.  It specifies language
bindings for C and Fortran.  This training covers the MPI 3.1 standard,
but also emphasizes potential pitfalls and best practices.

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


### Parallel programming with OpenMP (7 hours)

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


###Parallel programming with Threading Building Blocks (4 hours)

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
  * data-flow programming, task graphs
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

Supplementary material:

  * [Online reading material](https://gjbex.github.io/DPD-online-book/)


## Code optimization (4 hours)

For HPC applications, performance is a major concern.  A thorough
understanding of the relevant hardware and software components is
required.  In this training, you will learn about a number of these
components, and how they influence the efficiency of you application.
You will also learn how to profile your application to identify
performance bottlenecks.

For detailed information, see:
[https://gjbex.github.io/Code-optimization/](https://gjbex.github.io/Code-optimization/)



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

## HPC introduction (3 hours)

Although working on High Performance Computing (HPC) infrastructues is
not rocket science, there are still a number of things you need to be
aware of to do so efficiently.  Note that this session is specific for
(potential) users of the infrastructure managed by the Vlaams
Supercopmuting Centrum (VSC).

Subjects:

  * how to access the systems
  * architecture of a cluster
  * shared file systems
  * software stack
  * resource manageer and scheduler
  * accoutning
  
Prerequisites:

  * familiarity with the Linux command line

## Container for HPC (3 hours)

Singularity can be viewed as the Docker for HPC, i.e., a Singularity
image contains all the operating system/software components for your
application and can be deployed and run on HPC infrastructure, as well
as on your own laptop.

For detailed information, see:
[https://gjbex.github.io/Containers-for-HPC/](https://gjbex.github.io/Containers-for-HPC/)


## Worker and atools (3 hours)

Many scientific workloads are embarrassingly parallel, i.e, they can be broken
down into many independent computations.  Examples of such workflow are data
preprocessing or postprocesing of many files, or parameter exploration where
the same program is run for many different parameter instantiations.  Two
tools have been developed to help you minimize the hassle with such workloads.
This training session will highlight the strength of both tools, help you to
pick the right one for your workflow, and use it efficiently.

For detailed information, see:
[https://gjbex.github.io/worker-and-atools/](https://gjbex.github.io/worker-and-atools/)


## Version control with git (4 hours)

Version control is an essential part of the software development process
and is crucial for scientific application to help reproducibility.
You will learn how to use a version control system (either git or SVN)
to document the changes in your source code.

For detailed information, see:
[https://gjbex.github.io/Version-control-with-git/](https://gjbex.github.io/Version-control-with-git/)


# Code of conduct

Please note that by participating in any training listed here, either
online, hybrid, or face-to-face you implicitely agree to adhere tothe
[code of conduct](code_of_conduct.html).