LLVM Compiler Optimization Passes

For this assignment, we were tasked with making a couple of changes to the SimpleLICM
and DerivedInductionVar file provided. I made the following changes to the files found 
inside of llvm-tutor to complete our tasks. 

1. SimpleLICM: Loop-Invariant Code Motion using worklist algorithm
2. DerivedInductionVar: Induction Variable Elimination for nested loops

The location for SimpleLICM can be found at: lib/SimpleLICM.cpp

It is now able to identify and hoists loop invariant instructions out of loops to reduce
redundant computations
It uses a worklist approach for efficiency and identifies invariant instructions by looking 
at the operand dependencies. It will then hoists instructions to loop preheader and ensures
that the semantics and correctness are preserved. 

To test it, I have a test file that can be ran with the following line: 
opt -load-pass-plugin lib/libSimpleLICM.dylib -passes=simple-licm -S inputs/test_input.ll




The DerivedInductionVar file can be found at: lib/DerivedInductionVar.cpp

It is used to analyze and eliminate redundant induction variables found in nested loops
to have optimal memory usage and computation. It is the same concept we studied in class
where we saw we can use SCEV analysis to find the induction patterns. It uses SCEV to then 
perform the actual elimination of the induction variables. 

It can be tested by running the following line:

opt -load-pass-plugin lib/libDerivedInductionVar.dylib -passes=derived-iv -S inputs/nested_loop_test.ll


As mentioned, there are some test cases that I put to make sure the code works. 

For SimpleLICM:
inputs/test_licm.ll:  Basic loop-invariant code motion

For IVE Tests:

inputs/ive_test.ll: Basic induction variable patterns
inputs/nested_loop_test.ll Nested loop structures
inputs/complex_iv_test.ll: Multiple induction variables
inputs/edge_cases_test.ll: Complex usage patterns

These are some output examples that should be seen once running this code. 

Induction Variable Elimination for function: nested_loop_test
Analyzing loop: outer_loop
  Eliminated IV: i = {0,+,1}<outer_loop>
Analyzing loop: inner_loop
  Eliminated IV: j = {0,+,1}<inner_loop>
=== Summary: 1 loops, 2 IVs found, 2 eliminated ===


Another note is that I did not include the build file, which means it will have to be 
built as well following the same instructions as llvm-tutor