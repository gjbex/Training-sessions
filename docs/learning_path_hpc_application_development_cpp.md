# HPC application development: C++

If you want to develop HPC applications in C++, you can consider following the
following training sessions.

```mermaid
graph TD
  Best_practices_for_scientific_computing[Best practices for scientific computing] --> Version_control_with_git[Version control with Git]
  Best_practices_for_scientific_computing --> Linux_intro[Linux introduction]
  Linux_intro --> HPC_intro[HPC introduction]
  HPC_intro --> Containers_on_HPC[Containers on HPC]
  Best_practices_for_scientific_computing --> Scientific_Cpp[Scientific C++]
  Scientific_Cpp --> Cpp_software_engineering[C++ software engineering]
  Cpp_software_engineering --> Parallel_programming_with_STL_and_TBB[Parallel programming with STL and TBB]
  Cpp_software_engineering --> Parallel_programming_with_OpenMP[Parallel programming with OpenMP]
  Parallel_programming_with_OpenMP --> Parallel_programming_with_MPI[Parallel programming with MPI]
  Parallel_programming_with_STL_and_TBB --> Defensive_programming_and_debugging[Defensive programming and debugging]
  Parallel_programming_with_OpenMP --> Defensive_programming_and_debugging
  Parallel_programming_with_MPI --> Defensive_programming_and_debugging
  Defensive_programming_and_debugging --> Code_optimization[Code optimization]
  Parallel_programming_with_OpenMP --> GPU_programming[GPU programming]
  GPU_programming --> Code_optimization
  click Best_practices_for_scientific_computing "https://gjbex.github.io/Best-practices-for-scientific-computing/" "Best practices for scientific computing"
  click Version_control_with_git "https://gjbex.github.io/Version-control-with-git" "Version control with Git"
  click Linux_intro "https://gjbex.github.io/Training-sessions/linux_intro" "Linux introduction"
  click HPC_intro "https://gjbex.github.io/Training-sessions/hpc_intro" "HPC introduction"
  click Containers_on_HPC "https://gjbex.github.io/Containers-for-HPC/" "Containers on HPC"
  click Scientific_Cpp "https://gjbex.github.io/Scientific-C-plus-plus/" "Scientific C++"
  click Cpp_software_engineering "https://gjbex.github.io/C-plus-plus-software-engineering/" "C++ software engineering"
  click Defensive_programming_and_debugging "https://gjbex.github.io/Defensive-programming-and-debugging/" "Defensive programming and debugging"
  click Parallel_programming_with_STL_and_TBB "https://gjbex.github.io/Training-sessions/parallel_programming_with_stl_and_tbb" "Parallel programming with STL and TBB"
  click Parallel_programming_with_OpenMP "https://gjbex.github.io/Training-sessions/parallel_programming_with_openmp" "Parallel programming with OpenMP"
  click Parallel_programming_with_MPI "https://gjbex.github.io/Training-sessions/parallel_programming_with_mpi" "Parallel programming with MPI"
  click GPU_programming "https://gjbex.github.io/GPU-programming/" "GPU programming"
  click Code_optimization "https://gjbex.github.io/Code-optimization/" "Code optimization"
```

Start with the shared scientific-computing, Linux and HPC foundations if these
are new to you.  Then follow "[Scientific
C++](https://gjbex.github.io/Scientific-C-plus-plus/)" and "[C++ software
engineering](https://gjbex.github.io/C-plus-plus-software-engineering/)" to
build a maintainable application or library.

For parallelism, choose "[Parallel programming with STL and
TBB](parallel_programming_with_stl_and_tbb.md)" for modern C++ shared-memory
patterns, "[Parallel programming with OpenMP](parallel_programming_with_openmp.md)"
for directive-based shared-memory programming, and "[Parallel programming with
MPI](parallel_programming_with_mpi.md)" for distributed-memory systems.

For robust parallel development, continue with "[Defensive programming and
debugging](https://gjbex.github.io/Defensive-programming-and-debugging/)" to
learn how to test and debug shared-memory and MPI applications.

"[GPU programming](https://gjbex.github.io/GPU-programming/)" is an optional
branch when accelerators are part of your target system.  "[Code
optimization](https://gjbex.github.io/Code-optimization/)" is most useful after
you have a correct implementation, know which programming model you will use,
and have the debugging skills to validate changes.
