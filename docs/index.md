# Welcome to the training sessions overview


This is a (non-exhaustive) list of training sessions given by [Geert Jan
Bex](mailto:geertjan.bex@uhasselt.be), either offered on a regular basis by the
Vlaams Supercomputing Centrum (VSC) and EuroCC@Belgium, or on demand by
research institutes, governmental agencies and companies.

All of these training sessions can be tailored to the audience if required, and
ad-hoc training sessions are possible as well.

For many sessions, a dedicated website has been created that provides detailed
information, as well as a link to a GitHub repository that hosts the material
specific for that training.

For those sessions that do not yet have their own dedicated website, the
material can be found in the training-materials repository:
[https://github.com/gjbex/training-material](https://github.com/gjbex/training-material)

Many of the training sessions are organized in collaboration with the [Vlaams
Supercomputer Centrum (VSC)](https://www.vscentrum.be/) and
[EuroCC@Belgium](https://www.enccb.be/).  You can find the [schedule of
upcoming training sessions](https://www.vscentrum.be/training) on their
website.  For EuroCC training sessions, please consult the [EuroCC training
portal](https://hpc-portal.eu/training) on EuroCC ACCESS.

Below is a list of all the training sessions that are currently available.
A graphical overview of the training sessions on [computational
skills](computational_skills.md) is available.


# Training sessions

## C++

C++ is an important language for scientific programming and HPC.


### C++ for scientific programming (14 hours)

This training focuses on using C++ for scientific programming and on
the way Bjarne Stroustrup advocates modern C++ in his book "A tour of
C++".  Some C++17, C++20 and C++23 features and third party libraries
will also be discussed.

For detailed information, see:
[https://gjbex.github.io/Scientific-C-plus-plus/](https://gjbex.github.io/Scientific-C-plus-plus/)


### C++ software engineering

This training focuses on building applications and libraries in a
professional way using best practices in software engineering.

For detailed information, see:
[https://gjbex.github.io/C-plus-plus-software-engineering/](https://gjbex.github.io/C-plus-plus-software-engineering/)


### Parallel programming with the STL and Threading Building Blocks (3 hours)

Out of the box, the STL contains many algorithms that can be run in parallel.
In this training, you will learn how to do that, and what the performance
benefits may be.
Threading Building Blocks (TBB) is a C++ template library for developing
shared memory applications.  It integrates well with the C++ Standard
Template Library (STL) and can be used with any modern C++ compiler.
TBB is especially suited for nested parallelism, and pipe-lining when
part of the application can use accelerator hardware.

Subjects:

  * STL parallel algorithms
  * Threading Building Blocks
    * programming and execution model
    * recap of required C++ features
    * algorithms: `parallel_for`, `parallel_reduce`, `parallel_do`
    * task based programming
    * data-flow programming, task graphs
    * pitfalls and best practices

Prerequisites:

  * experience in C++ programming


### Other training sessions useful for C++ programmers

  * Parallel programming with OpenMP
  * Parallel programming with MPI
  * OpenMP GPU offloading
  * Heterogeneous programming with Kokkos
  * Code optimization
  * Defensive programming and debugging
  * Best practices in scientific programming
  * Version control with git


## Fortran programming

### Fortran for programmers (8 hours)

Fortran is used a lot in the context of HPC.  For many, it has a
reputation of being an old and ugly programming language.  However,
modern Fortran is a far cry from Fortran 77 that its detractors have
in mind.  Fortran 2003/2008 is a language that is well tailored
towards scientific computing.  This training introduces the language
and its features.

For detailed information, see:
[https://gjbex.github.io/Fortran-for-programmers/](https://gjbex.github.io/Fortran-for-programmers/)


### Other training sessions useful for Fortran programmers

  * Parallel programming with OpenMP
  * Parallel programming with MPI
  * OpenMP GPU offloading
  * Code optimization
  * Defensive programming and debugging
  * Best practices in scientific programming
  * Version control with git


## C programming

C is still a very popular programming language, also in the
context of scientific programming and HPC.

### Scientific C (12 hours)

C is still one of the more popular programming languages today.  It is
probably mainly used for systems programming, but there are also many
applications for scientific computing that have been developed in this
programming language.

For detailed information, see:
[https://gjbex.github.io/Scientific-C/](https://gjbex.github.io/Scientific-C/)

### Other training sessions useful for C programmers

  * Parallel programming with OpenMP
  * Parallel programming with MPI
  * OpenMP GPU offloading
  * Code optimization
  * Defensive programming and debugging
  * Best practices in scientific programming
  * Version control with git


## Python training sessions

Python is a versatile programming language that is used in many domains.


### Python for beginners (16 hours)

Python is a versatile programming language that is used in many domains.
It is easy to learn.  This training material introduces the basics, and
can be used for self-study, or as a basis for training sessions.  It 
requires no prior programming experience.

For detailed information, see:
[https://gjbex.github.io/Python-for-beginners/](https://gjbex.github.io/Python-for-beginners/)


### Python for programmers (4 hours)

Python is an all-round programming language that has applications in
many domains.  This training session introduces the programming
language to participants who have programming experience with other
programming languages such as R, MATLAB, C/C++ or Fortran.

For detailed information, see:
[https://gjbex.github.io/Python-for-programmers/](https://gjbex.github.io/Python-for-programmers/)


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


### Machine learning with Python (4 hours)

Python is one of the dominant languages in the area of machine learning
and AI.  This training will provide an introduction to machine learning
methodology for data preparation and machine learning, as well as some
machine learning algorithms.

For detailed information, see:
[https://gjbex.github.io/Machine-learning-with-Python/](https://gjbex.github.io/Machine-learning-with-Python/)


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


### Python dashboards (2 hours)

Dashboards are a useful way to present data in an interactive way.  They can be used
for reporting, but also for data exploration, or even to create simple web applications.
You can run dashboards locally, or deploy them via GitHub or GitLab, or even on a
server in the cloud.  Creating dashboards in Python is quite straightforward.  In this
training you will learn about several frameworks and their strengths and weaknesses.

For detailed information, see:
[https://gjbex.github.io/Python-dashboards/](https://gjbex.github.io/Python-dashboards/)


### Python systems programming (4 hours)

Python is a very versatile programming language that has a wide range of
applications.  This training concentrates on interaction with the
operating system, the file system, other applications and the network.
This is useful for systems programming, but also when you want to use
Python as a coordination language for your workflows.
This training introduces modules that are useful in that context.

For detailed information, see:
[https://gjbex.github.io/Python-for-systems-programming/](https://gjbex.github.io/Python-for-systems-programming/)


### Other training sessions useful for Python programmers

  * Parallel programming with MPI
  * Best practices in scientific programming
  * Version control with git
  * Jupyter notebooks


## Julia: the good, the bad and the ugly (4 hours)

Julia has gained quite some traction over the last couple of years, but is it for you?
In this training you will see how it compares to MATLAB and Python, and what Julia's
strong and weak points are.

For detailed information, see:
[https://gjbex.github.io/Julia_good_bad_ugly/](https://gjbex.github.io/Julia_good_bad_ugly/)


## Jupyter notebooks (3 hours)

Jupyter notebooks are a versatile tools for data exploration and
exploratory programming in a wide variety of programming languages. In this
session you will learn how to use Jupyter Notebooks effectively.

For details on Jupyter notebooks, see:
[https://gjbex.github.io/Jupyter-notebooks/](https://gjbex.github.io/Jupyter-notebooks/)


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

  * experience in C, C++, Fortran or Python programming;
  * for the section on hybrid programming, notions of OpenMP are required.


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

  * experience in C, C++, or Fortran.


## OpenMP GPU offloading (4 hours)

GPUs are used more and more in scientific computing, data science and
machine learning.  This training will introduce you to using hardware-agnostic
programming using OpenMP to offload computations to GPUs.

For detailed information, see:
[https://gjbex.github.io/GPU-programming/](https://gjbex.github.io/GPU-programming/)


## Heterogeneous programming with Kokkos (8 hours)

Kokkos is a C++ library that enables writing performance portable code
for heterogeneous systems.  It can offload to accelerators such as GPUs.

For detailed information, see:
[https://gjbex.github.io/GPU-programming/](https://gjbex.github.io/GPU-programming/)


## Defensive programming and debugging (4 hours + 2 hours optional)

All code contains bugs, finding and fixing them is boring.  In this
training, best practices are presented to reduce the number of bugs
in your code.  You will also learn about debuggers and debugging
techniques to find bugs more efficiently.

For detailed information, see:
[https://gjbex.github.io/Defensive-programming-and-debugging/](https://gjbex.github.io/Defensive-programming-and-debugging/)

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


## Best practices for scientific computing (4 hours)

As a scientist, your core business is science, not software engineering.
Nevertheless, having a good understanding of how best practices in software
engineering can help you work more efficiently, or give your work more
exposure is quite useful.  This training is flexible in that it can be
tailored to any combination of C, C++, Fortran or Python, and to many
levels of detail.

Subjects:

  * code style
  * version control & collaboration
  * testing
    * unit testing
    * functional testing
    * code coverage
  * documentation
  * deployment
  * continuous integration

Prerequisites:

  * fluency in at least one programming language

Supplementary material:

  * [website](https://gjbex.github.io/Best-practices-for-scientific-computing/)


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

Although working on High Performance Computing (HPC) infrastructures is
not rocket science, there are still a number of things you need to be
aware of to do so efficiently.  Note that this session is specific for
(potential) users of the infrastructure managed by the Vlaams
Supercomputing Centrum (VSC).

Subjects:

  * how to access the systems
  * architecture of a cluster
  * shared file systems
  * software stack
  * resource manager and scheduler
  * accounting
  
Prerequisites:

  * familiarity with the Linux command line


## Best practices for data science on HPC (4 hours)

Although it seems that running data science workflows on HPC systems is
quite straightforward, there are quite a number of pitfalls and best practices
that you need to be aware of.

Subjects:

  * how to fine-tune your data science workflow for HPC
  * data formats and I/O
  * distributed computing

Prerequisites:

  * familiarity with the Linux command line
  * familiarity with the basics of HPC systems
  * familiarity with R or Python


## Container for HPC (4 hours)

Singularity can be viewed as the Docker for HPC, i.e., a Singularity
image contains all the operating system/software components for your
application and can be deployed and run on HPC infrastructure, as well
as on your own laptop.

For detailed information, see:
[https://gjbex.github.io/Containers-for-HPC/](https://gjbex.github.io/Containers-for-HPC/)


## Workflows for HPC (4 hours)

The HPC ecosystems provides numerous tools to help you manage your
workflows.  In this training, you will learn about some of these tools,
and how to use them effectively.

For detailed information, see:
[https://gjbex.github.io/Workflows-for-HPC/](https://gjbex.github.io/Workflows-for-HPC/)


## MLOps on HPC (4 hours)

MLOps is a set of practices that aims to deploy and maintain machine learning
models reproducibly, reliably and efficiently.  In this training you will learn
how to use MLOps tools on HPC systems.  In fact, this training is also for you
if you perform any kind of computational experiments, not just machine learning.

For detailed information, see:
[https://gjbex.github.io/MLOps-on-HPC/](https://gjbex.github.io/MLOps-on-HPC/)


## Version control with git (4 hours)

Version control is an essential part of the software development process
and is crucial for scientific application to help reproducibility.
You will learn how to use a version control system (either git or SVN)
to document the changes in your source code.

For detailed information, see:
[https://gjbex.github.io/Version-control-with-git/](https://gjbex.github.io/Version-control-with-git/)


## Generative AI for software engineering and data analysis (3 hours)

Generative AI is a useful tool in software engineering and data analysis. However,
if you want to use it effectively, you need to understand the basics of the
underlying technology, and to be aware of potential pitfalls..

After an introduction to the basics of generative AI, various applications will be
demoed, and you will be able to experiment with some of them yourself.  Tools such
as OpenAI's Chat-GPT and GitHub's Copilot will be discussed.

Prerequisites:

  * experience in some programming language;
  * familiarity with the Linux command line


## Deploying LLMs locally (4 hours)

Large/Small Language Models are very useful tools in software engineering and
data analysis. However, if you want to use them effectively, you need to
understand the basics of the underlying technology, and to be aware of
potential pitfalls.  In many situations it is useful to deploy a LLM locally,
rather than using a cloud service.  This training will show you how to do that.

For detailed information, see:
[https://gjbex.github.io/Deploying-LLMs-locally/](https://gjbex.github.io/Deploying-LLMs-locally/)


## Scientific visualization with ParaView (2 hours)

ParaView is an open-source, multi-platform data analysis and visualization
tools for scientific data.  In this training you will learn how to use
ParaView to visualize your data.

Prerequisites:

  * none


# Code of conduct

Please note that by participating in any training listed here, either
online, hybrid, or face-to-face you implicitly agree to adhere to the
[code of conduct](code_of_conduct.md).


# License

All the training materials are licensed under the [Creative Commons Attribution
4.0 International License](https://creativecommons.org/licenses/by/4.0/).
