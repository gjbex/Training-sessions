# Parallel programming with the STL and Threading Building Blocks (3 hours)

Out of the box, the STL contains many algorithms that can be run in parallel.
In this training, you will learn how to do that, and what the performance
benefits may be.
Threading Building Blocks (TBB) is a C++ template library for developing
shared memory applications.  It integrates well with the C++ Standard
Template Library (STL) and can be used with any modern C++ compiler.
TBB is especially suited for nested parallelism, and pipelining when
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
