# Software engineering

Good practices in software engineering will contribute considerably to the
quality of your scientific software.

```mermaid
graph TD
  Best_practices_for_scientific_computing[Best practices for scientific computing] --> Version_control_with_git[Version control with git]
  Best_practices_for_scientific_computing --> Containers_on_HPC[Containers on HPC]
  Best_practices_for_scientific_computing --> Programming[Programming]
  Programming --> Defensive_programming_and_debugging[Defensive programming and debugging]
  Defensive_programming_and_debugging --> Code_optimization[Code optimization]
  Programming --> Code_optimization
  Programming --> Generative_AI_in_software_engineering_and_data_analysis[Generative AI in software engineering and data analysis]
  Code_optimization --> Parallel_computing[Parallel computing]
  Code_optimization --> GPU_computing[GPU computing]
  click Best_practices_for_scientific_computing "https://gjbex.github.io/Training-sessions/best_practices_for_scientific_computing" "Best practices for scientific computing"
  click Version_control_with_git "https://gjbex.github.io/Version-control-with-git/" "Version control with git"
  click Containers_on_HPC "https://gjbex.github.io/Containers-for-HPC/" "Containers on HPC"
  click Programming "https://gjbex.github.io/Training-sessions/programming" "Programming"
  click Defensive_programming_and_debugging "https://gjbex.github.io/Defensive_programming_and_debugging/" "Defensive programming and debugging"
  click Code_optimization "https://gjbex.github.io/Code-optimization/" "Code optimization"
  click Parallel_computing "https://gjbex.github.io/Training-sessions/parallel_computing" "Parallel computing"
  click GPU_computing "https://gjbex.github.io/Training-sessions/gpu_computing" "GPU computing"
  click Generative_AI_in_software_engineering_and_data_analysis "https://gjbex.github.io/Training-sessions/generative_ai_in_software_engineering_and_data_analysis" "Generative AI in software engineering and data analysis"
```

If you are new to software engineering in the context of scientific computing,
you may want to start with "[Best practices for scientific
computing](best_practices_for_scientific_computing.md)".

Of course, you coding skills should be up to par.  For more information on this
topic, see "[Programming](programming.md)".

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
debugging](https://gjbex.github.io/Defensive_programming_and_debugging)".

Effectively optimizing your code implies that you have a thorough understanding
of the hardware you are using and how your code interacts with it.  For more
information on this topic, see "[Code optimization](https://gjbex.github.io/Code-optimization)".

Parallel or GPU computing is often required to take full advantage of modern
compute nodes.  For more information on this topic, see "[Parallel
computing](parallel_computing.md)" and "[GPU computing](gpu_computing.md)".
