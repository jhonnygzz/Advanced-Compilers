; LICM test: multiple invariants, some dependent on others
; Should hoist %c1, %c2, and %c3

define void @test_licm2(i32 %N, i32 %M) {
entry:
  br label %loop

loop:
  %i = phi i32 [0, %entry], [%i_next, %loop]
  %c1 = add i32 %N, 10         ; loop-invariant
  %c2 = mul i32 %c1, %M        ; loop-invariant, depends on %c1
  %c3 = sub i32 %c2, 5         ; loop-invariant, depends on %c2
  %idx = add i32 %i, %c3       ; not invariant (depends on i)
  %i_next = add i32 %i, 1
  %cond = icmp slt i32 %i_next, %N
  br i1 %cond, label %loop, label %exit

exit:
  ret void
}
