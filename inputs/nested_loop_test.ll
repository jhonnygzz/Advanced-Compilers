; Test nested loops for DerivedInductionVar analysis
define void @nested_loop_test(i32 %N) {
entry:
  br label %outer_loop

outer_loop:
  %i = phi i32 [0, %entry], [%i_next, %outer_end]
  %i_mul2 = mul i32 %i, 2
  br label %inner_loop

inner_loop:
  %j = phi i32 [0, %outer_loop], [%j_next, %inner_loop]
  %j_add5 = add i32 %j, 5
  %val = add i32 %i_mul2, %j_add5
  %j_next = add i32 %j, 1
  %inner_cond = icmp slt i32 %j_next, 10
  br i1 %inner_cond, label %inner_loop, label %outer_end

outer_end:
  %i_next = add i32 %i, 1
  %outer_cond = icmp slt i32 %i_next, %N
  br i1 %outer_cond, label %outer_loop, label %exit

exit:
  ret void
}