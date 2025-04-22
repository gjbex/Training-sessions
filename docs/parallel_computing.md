# Parallel computing

Parallel computing will help to exploit the full potential of modern hardware
in general and HPC systems in particular.

```mermaid
graph LR
  Parallel_programming_with_OpenMP[Parallel programming with OpenMP] --> Parallel_programming_with_MPI[Parallel programming with MPI]
  Parallel_programming_with_OpenMP[Parallel programming with OpenMP] --> GPU_offloading_with_OpenMP[GPU offloading with OpenMP]
  Python_on_HPC[Python on HPC] --> Parallel_programming_with_MPI
  Parallel_programming_with_STL_and_TBB[Parallel programming with STL and TBB]
  click Parallel_programming_with_OpenMP "https://gjbex.github.io/Training-sessions/parallel_programming_with_openmp" "Parallel programming with OpenMP"
  click Parallel_programming_with_MPI "https://gjbex.github.io/Training-sessions/parallel_programming_with_mpi" "Parallel programming with MPI"
  click Python_on_HPC "https://gjbex.github.io/Python-for-HPC/" "Python on HPC"
  click Parallel_programming_with_STL_and_TBB "https://gjbex.github.io/Training-sessions/parallel_programming_with_stl_and_tbb" "Parallel programming with STL and TBB"
  click GPU_offloading_with_OpenMP "https://gjbex.github.io/GPU-programming/" "GPU offloading with OpenMP"
```
