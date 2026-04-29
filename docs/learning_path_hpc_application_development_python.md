# HPC application development: Python

If you want to develop HPC applications using Python, you can consider following the
following training sessions.


```mermaid
graph TD
  Python_for_beginners[Python for beginners] --> Python_for_programmers[Python for programmers]
  Linux_intro[Linux introduction] --> HPC_intro[HPC introduction]
  Python_for_programmers --> Scientific_Python[Scientific Python]
  HPC_intro --> Python_for_HPC[Python for HPC]
  Python_for_programmers --> Python_software_engineering[Python software engineering]
  Version_control_with_git[Version control with Git] --> Python_software_engineering
  Python_software_engineering --> Python_for_HPC
  Scientific_Python --> Python_for_HPC[Python for HPC]
  Python_for_HPC -. optional .-> Scientific_Cpp[Scientific C++]
  Python_for_HPC -. optional .-> Python_on_GPUs[Python on GPUs]
  Python_for_HPC -. optional .-> Parallel_programming_with_MPI[Parallel programming with MPI]
  classDef optional fill:#f7f7f7,stroke:#777,stroke-dasharray: 4 4,color:#333
  class Scientific_Cpp,Python_on_GPUs,Parallel_programming_with_MPI optional
  click Version_control_with_git "https://gjbex.github.io/Version-control-with-git" "Version control with Git"
  click Linux_intro "https://gjbex.github.io/Training-sessions/linux_intro" "Linux introduction"
  click HPC_intro "https://gjbex.github.io/Training-sessions/hpc_intro" "HPC introduction"
  click Python_for_beginners "https://gjbex.github.io/Python-for-beginners/" "Python for beginners"
  click Python_for_programmers "https://gjbex.github.io/Python-for-programmers/" "Python for programmers"
  click Python_software_engineering "https://gjbex.github.io/Python-software-engineering/" "Python software engineering"
  click Scientific_Python "https://gjbex.github.io/Scientific-Python/" "Scientific Python"
  click Python_for_HPC "https://gjbex.github.io/Python-for-HPC/" "Python for HPC"
  click Scientific_Cpp "https://gjbex.github.io/Scientific-C-plus-plus/" "Scientific C++"
  click Python_on_GPUs "https://gjbex.github.io/Python-on-GPUs/" "Python on GPUs"
  click Parallel_programming_with_MPI "https://gjbex.github.io/Training-sessions/parallel_programming_with_mpi" "Parallel programming with MPI"
```

Dashed arrows indicate optional branches.

If you are new to programming, start with "[Python for
beginners](https://gjbex.github.io/Python-for-beginners)" to learn the basics.
This is a preparatory training session.  To reach the level needed for the rest
of this path, continue with "[Python for
programmers](https://gjbex.github.io/Python-for-programmers)", which goes into
more detail and is the real starting point for HPC Python development.  If you
already have programming experience in another language, you can start directly
with "[Python for programmers](https://gjbex.github.io/Python-for-programmers)".

Since you will be working on HPC systems, you should be familiar with the
"[Linux introduction](https://gjbex.github.io/Training-sessions/linux_intro)"
and "[HPC introduction](https://gjbex.github.io/Training-sessions/hpc_intro)"
training sessions.

For scientific applications, continue with "[Scientific
Python](https://gjbex.github.io/Scientific-Python)" to learn the core Python
libraries used for numerical and scientific computing.

For maintainable HPC Python applications, follow "[Version control with
git](https://gjbex.github.io/Version-control-with-git)" and "[Python software
engineering](https://gjbex.github.io/Python-software-engineering)".  These
topics become important once your code needs to be shared, installed, tested,
documented, or reused.

"[Python for HPC](https://gjbex.github.io/Python-for-HPC)" is the central
training in this path.  It focuses on writing efficient Python code for HPC
systems and on understanding when Python code should use optimized libraries,
parallel execution, or compiled extensions.

If you intend to interface Python with C++ code, you may want to follow
"[Scientific C++](https://gjbex.github.io/Scientific-C-plus-plus)" as an
optional branch.

If you want to use accelerators from Python, follow "[Python on
GPUs](https://gjbex.github.io/Python-on-GPUs/)".  If your Python application
uses distributed-memory parallelism, follow "[Parallel programming with
MPI](parallel_programming_with_mpi.md)".
