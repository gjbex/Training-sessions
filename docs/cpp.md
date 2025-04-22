# C++ programming

C++ is an important language for scientific programming and HPC.

```mermaid
graph TD
  Scientific_Cpp[Scientific C++] --> Cpp_software_engineering[C++ software engineering]
  Cpp_software_engineering --> Defensive_programming_and_debugging[Defensive programming and debugging]
  Cpp_software_engineering --> Code_optimization[Code optimization]
  Defensive_programming_and_debugging --> Code_optimization
  Code_optimization --> Parallel_programming_with_OpenMP[Parallel programming with OpenMP]
  Code_optimization --> Parallel_programming_with_MPI[Parallel programming with MPI]
  Parallel_programming_with_OpenMP --> Parallel_programming_with_MPI
  Code_optimization --> GPU_programming[GPU programming]
  Code_optimization --> Parallel_programming_with_STL_and_TBB[Parallel programming with STL and TBB]
  Parallel_programming_with_OpenMP --> GPU_programming
  click Scientific_Cpp "https://gjbex.github.io/Scientific-C-plus-plus/" "Scientific C++"
  click Cpp_software_engineering "https://gjbex.github.io/C-plus-plus-software-engineering/" "C++ software engineering"
  click Defensive_programming_and_debugging "https://gjbex.github.io/Defensive_programming_and_debugging/" "Defensive programming and debugging"
  click Code_optimization "https://gjbex.github.io/Code-optimization/" "Code optimization"
  click Parallel_programming_with_OpenMP "https://gjbex.github.io/Training-sessions/parallel_programming_with_openmp" "Parallel programming with OpenMP"
  click Parallel_programming_with_MPI "https://gjbex.github.io/Training-sessions/parallel_programming_with_mpi" "Parallel programming with MPI"
  click GPU_programming "https://gjbex.github.io/GPU-programming/" "GPU programming"
  click Parallel_programming_with_STL_and_TBB "https://gjbex.github.io/Training-sessions/parallel_programming_with_stl_and_tbb" "Parallel programming with STL and TBB"
```
