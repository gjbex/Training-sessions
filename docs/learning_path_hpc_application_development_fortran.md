# HPC application development: Fortran

If you want to develop HPC applications in Fortran, you can consider following
the following training sessions.

```mermaid
graph TD
  Best_practices_for_scientific_computing[Best practices for scientific computing] --> Version_control_with_git[Version control with Git]
  Best_practices_for_scientific_computing --> Linux_intro[Linux introduction]
  Linux_intro --> HPC_intro[HPC introduction]
  HPC_intro --> Containers_on_HPC[Containers on HPC]
  Best_practices_for_scientific_computing --> Fortran_for_programmers[Fortran for programmers]
  Fortran_for_programmers --> Parallel_programming_with_OpenMP[Parallel programming with OpenMP]
  Parallel_programming_with_OpenMP --> Parallel_programming_with_MPI[Parallel programming with MPI]
  Parallel_programming_with_OpenMP --> Defensive_programming_and_debugging[Defensive programming and debugging]
  Parallel_programming_with_MPI --> Defensive_programming_and_debugging
  Defensive_programming_and_debugging --> Code_optimization[Code optimization]
  Parallel_programming_with_OpenMP --> GPU_programming[GPU programming]
  GPU_programming --> Code_optimization
  click Best_practices_for_scientific_computing "https://gjbex.github.io/Best-practices-for-scientific-computing/" "Best practices for scientific computing"
  click Version_control_with_git "https://gjbex.github.io/Version-control-with-git" "Version control with Git"
  click Linux_intro "https://gjbex.github.io/Training-sessions/linux_intro" "Linux introduction"
  click HPC_intro "https://gjbex.github.io/Training-sessions/hpc_intro" "HPC introduction"
  click Containers_on_HPC "https://gjbex.github.io/Containers-for-HPC/" "Containers on HPC"
  click Fortran_for_programmers "https://gjbex.github.io/Fortran-for-programmers/" "Fortran for programmers"
  click Defensive_programming_and_debugging "https://gjbex.github.io/Defensive-programming-and-debugging/" "Defensive programming and debugging"
  click Parallel_programming_with_OpenMP "https://gjbex.github.io/Training-sessions/parallel_programming_with_openmp" "Parallel programming with OpenMP"
  click Parallel_programming_with_MPI "https://gjbex.github.io/Training-sessions/parallel_programming_with_mpi" "Parallel programming with MPI"
  click GPU_programming "https://gjbex.github.io/GPU-programming/" "GPU programming"
  click Code_optimization "https://gjbex.github.io/Code-optimization/" "Code optimization"
```

Start with the shared scientific-computing, Linux and HPC foundations if these
are new to you.  Then follow "[Fortran for
programmers](https://gjbex.github.io/Fortran-for-programmers/)" to build a
modern Fortran foundation for scientific programming.

After that, choose "[Parallel programming with
OpenMP](parallel_programming_with_openmp.md)" for shared-memory nodes and
"[Parallel programming with MPI](parallel_programming_with_mpi.md)" for
distributed-memory systems.

For production-quality parallel Fortran applications, continue with
"[Defensive programming and
debugging](https://gjbex.github.io/Defensive-programming-and-debugging/)" to
learn how to test and debug shared-memory and MPI applications.

"[GPU programming](https://gjbex.github.io/GPU-programming/)" is an optional
branch when accelerators are part of your target system.  "[Code
optimization](https://gjbex.github.io/Code-optimization/)" is most useful after
you have a correct implementation, know which programming model you will use,
and have the debugging skills to validate changes.
