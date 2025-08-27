# HPC python application development learning path

If you want to develop HPC applications using Python, you can consider following the
following training sessions.


```mermaid
graph TD
  Python_for_beginners[Python for beginners] --> Python_for_programmers[Python for programmers]
  Version_control_with_git[Version control with Git] --> Python_for_programmers
  Linux_intro[Linux introduction] --> HPC_intro[HPC introduction]
  Python_for_programmers --> Scientific_python[Scientific Python]
  Linux_intro[Linux introduction] --> HPC_intro[HPC introduction]
  HPC_intro --> Python_for_HPC[Python for HPC]
  Python_for_programmers --> Python_software_engineering[Python software engineering]
  Scientific_Python --> Python_for_HPC[Python for HPC]
  Scientific_Cpp[Scientific C++] --> Python_for_HPC
  click Version_control_with_git "https://gjbex.github.io/Version-control-with-git" "Version control with Git"
  click Linux_intro "https://gjbex.github.io/Training-sessions/linux_intro" "Linux introduction"
  click HPC_intro "https://gjbex.github.io/Training-sessions/hpc_intro" "HPC introduction"
  click Python_for_beginners "https://gjbex.github.io/Python-for-beginners/" "Python for beginners"
  click Python_for_programmers "https://gjbex.github.io/Python-for-programmers/" "Python for programmers"
  click Python_software_engineering "https://gjbex.github.io/Python-software-engineering/" "Python software engineering"
  click Scientific_Python "https://gjbex.github.io/Scientific-Python/" "Scientific Python"
  click Python_for_HPC "https://gjbex.github.io/Python-for-HPC/" "Python for HPC"
  click Scientific_Cpp "https://gjbex.github.io/Scientific-C-plus-plus/" "Scientific C++"
```

If you are new to development using Python, you may want to start with
"[Python for beginners](https://gjbex.github.io/Python-for-beginners)" and
"[Python for programmers](https://gjbex.github.io/Python-for-programmers)".

It is important that you improve you software engineering skills, so you may want to
follow the "[Python software engineering](https://gjbex.github.io/Python-software-engineering)" and
"[Version control with git](https://gjbex.github.io/Version-control-with-git)" training sessions.

Python has a rich ecosystem of libraries for scientific computing, so you may want to
follow the "[Scientific Python](https://gjbex.github.io/Scientific-Python)" training session.

Since you will be working on HPC systems, you need to be familiar with the
"[Linux introduction](https://gjbex.github.io/Training-sessions/linux_intro)" and
"[HPC introduction](https://gjbex.github.io/Training-sessions/hpc_intro)" training sessions.

Finally, you may want to follow the "[Python for HPC](https://gjbex.github.io/Python-for-HPC)"
training session to learn how to write efficient Python code for HPC systems.

If you intend to interface Python with C++ code, you may want to follow the
"[Scientific C++](https://gjbex.github.io/Scientific-C-plus-plus)" training session as well.
