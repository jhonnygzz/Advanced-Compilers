; Test for DerivedInductionVar elimination (IVE)
; The PHI %i should be eliminated and replaced with its closed-form

define void @ive_test(i32 %N) {
entry:
  br label %loop

loop:
  %i = phi i32 [0, %entry], [%i_next, %loop]
  %val = add i32 %i, 1
  %i_next = add i32 %i, 1
  %cond = icmp slt i32 %i_next, %N
  br i1 %cond, label %loop, label %exit

exit:
  ret void
}
