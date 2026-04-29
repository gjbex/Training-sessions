# Using HPC applications learning path

If you want to run HPC applications, you can consider following the
following training sessions.


```mermaid
graph TD
  Best_practices_for_scientific_computing[Best practices for scientific computing] --> Version_control_with_git[Version control with Git]
  Best_practices_for_scientific_computing[Best practices for scientific computing] --> Linux_intro[Linux introduction]
  Linux_intro --> HPC_intro[HPC introduction]
  HPC_intro --> Workflows_for_HPC[Workflows for HPC]
  HPC_intro --> Containers_on_HPC[Containers on HPC]
  HPC_intro --> MLOps_on_HPC[MLOps on HPC]
  click Best_practices_for_scientific_computing "https://gjbex.github.io/Best-practices-for-scientific-computing/" "Best practices for scientific computing"
  click Version_control_with_git "https://gjbex.github.io/Version-control-with-git" "Version control with Git"
  click Linux_intro "https://gjbex.github.io/Training-sessions/linux_intro" "Linux introduction"
  click HPC_intro "https://gjbex.github.io/Training-sessions/hpc_intro" "HPC introduction"
  click Workflows_for_HPC "https://gjbex.github.io/Workflows-for-HPC/" "Workflows for HPC"
  click Containers_on_HPC "https://gjbex.github.io/Containers-for-HPC/" "Containers on HPC"
  click MLOps_on_HPC "https://gjbex.github.io/MLOps-on-HPC/" "MLOps on HPC"
```

If you are new to running HPC applications in the context of scientific
computing, you may want to start with "[Best practices for scientific
computing](best_practices_for_scientific_computing.md)".

The next step is to familiarize yourself with the basics of working on the
[Linux command line](https://gjbex.github.io/Training-sessions/linux_intro) and
the [HPC infrastructure](https://gjbex.github.io/Training-sessions/hpc_intro).

Version control is an essential part of reproducible scientific research.  For
more information on this topic, see "[Version control with
git](https://gjbex.github.io/Version-control-with-git)".

Depending on the HPC application you want to run, you may want to learn about
"[Workflows for HPC](https://gjbex.github.io/Workflows-for-HPC/)" to automate
multi-step analyses, "[Containers on
HPC](https://gjbex.github.io/Containers-for-HPC/)" to manage software
environments, or "[MLOps on HPC](https://gjbex.github.io/MLOps-on-HPC/)" when
your work involves machine learning experiments.
