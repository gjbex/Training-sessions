# HPC application development learning path

If you want to develop HPC applications, you can consider following the
following training sessions.


```mermaid
graph TD
  Best_practices_for_scientific_computing[Best practices for scientific computing] --> Version_control_with_git[Version control with Git]
  Best_practices_for_scientific_computing[Best practices for scientific computing] --> Linux_intro[Linux introduction]
  Linux_intro --> HPC_intro[HPC introduction]
  HPC_intro --> Containers_on_HPC[Containers on HPC]
  Best_practices_for_scientific_computing --> Programming[Programming]
  Programming --> Scientific_C[Scientific C]
  Programming --> Scientific_Cpp[Scientific C++]
  Programming --> Fortran_for_programmers[Fortran for programmers]
  Programming --> Python_for_HPC_applications[Python HPC application development]
  Programming --> Defensive_programming_and_debugging[Defensive programming and debugging]
  Defensive_programming_and_debugging --> Code_optimization[Code optimization]
  Programming --> Code_optimization
  Programming --> Generative_ai_for_software_engineering_and_data_analysis[Generative AI in software\nengineering and data analysis]
  HPC_intro --> Defensive_programming_and_debugging
  Scientific_C --> Parallel_computing[Parallel computing]
  Scientific_Cpp --> Parallel_computing
  Fortran_for_programmers --> Parallel_computing
  Python_for_HPC_applications --> Parallel_computing
  Parallel_computing --> GPU_computing[GPU computing]
  Parallel_computing --> Code_optimization
  GPU_computing --> Code_optimization
  click Best_practices_for_scientific_computing "https://gjbex.github.io/Best-practices-for-scientific-computing/" "Best practices for scientific computing"
  click Version_control_with_git "https://gjbex.github.io/Version-control-with-git" "Version control with Git"
  click Linux_intro "https://gjbex.github.io/Training-sessions/linux_intro" "Linux introduction"
  click HPC_intro "https://gjbex.github.io/Training-sessions/hpc_intro" "HPC introduction"
  click Containers_on_HPC "https://gjbex.github.io/Containers-for-HPC/" "Containers on HPC"
  click Generative_ai_for_software_engineering_and_data_analysis "https://gjbex.github.io/Training-sessions/generative_ai_for_software_engineering_and_data_analysis" "Generative AI in software\nengineering and data analysis"
  click Programming "https://gjbex.github.io/Training-sessions/programming" "Programming"
  click Scientific_C "https://gjbex.github.io/Scientific-C/" "Scientific C"
  click Scientific_Cpp "https://gjbex.github.io/Scientific-C-plus-plus/" "Scientific C++"
  click Fortran_for_programmers "https://gjbex.github.io/Fortran-for-programmers/" "Fortran for programmers"
  click Python_for_HPC_applications "https://gjbex.github.io/Training-sessions/learning_path_developing_python_hpc_applications" "Python HPC application development"
  click Defensive_programming_and_debugging "https://gjbex.github.io/Defensive-programming-and-debugging/" "Defensive programming and debugging"
  click Code_optimization "https://gjbex.github.io/Code-optimization/" "Code optimization"
  click Parallel_computing "https://gjbex.github.io/Training-sessions/parallel_computing" "Parallel computing"
  click GPU_computing "https://gjbex.github.io/Training-sessions/gpu_computing" "GPU computing"
```

If you are new to software development in the context of scientific computing,
you may want to start with "[Best practices for scientific
computing](best_practices_for_scientific_computing.md)".

The next step is to familiarize yourself with the basics of working on the
[Linux command line](https://gjbex.github.io/Training-sessions/linux_intro) and
the [HPC infrastructure](https://gjbex.github.io/Training-sessions/hpc_intro).

Of course, your coding skills should be up to par.  For more information on
this topic, see "[Programming](programming.md)".  Depending on the language you
use, you can continue with "[Scientific C](https://gjbex.github.io/Scientific-C/)",
"[Scientific C++](https://gjbex.github.io/Scientific-C-plus-plus/)",
"[Fortran for programmers](https://gjbex.github.io/Fortran-for-programmers/)",
or the "[Python HPC application development
path](learning_path_developing_python_hpc_applications.md)".

Version control is an essential part of software engineering.  For more
information on this topic, see "[Version control with
git](https://gjbex.github.io/Version-control-with-git)".

[Containers](https://gjbex.github.io/Containers-for-HPC) are useful tools in
the context of software engineering both to create a complete, stable and
portable development environment, but also as a means to distribute your
software.

Writing robust code that has been well-tested is an essential part of software
development.  Having tests in place is also essential when trying to optimize
your code.  For more information on this topic, see "[Defensive programming and
debugging](https://gjbex.github.io/Defensive-programming-and-debugging)".

Parallel or GPU computing is often required to take full advantage of modern
compute nodes.  For more information on this topic, see "[Parallel
computing](parallel_computing.md)" and "[GPU computing](gpu_computing.md)".

Effectively optimizing your code implies that you understand the programming
model, the hardware you are using, and how your code interacts with it.  For
more information on this topic, see "[Code
optimization](https://gjbex.github.io/Code-optimization)".
