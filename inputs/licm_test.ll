; Simple loop-invariant code for LICM testing
; This loop has invariant instructions that should be hoisted

define void @test_licm(ptr %A, i32 %N) {
entry:
  br label %loop

loop:
  %i = phi i32 [0, %entry], [%i_next, %loop]
  %c1 = add i32 %N, 42        ; loop-invariant
  %c2 = mul i32 %N, 2         ; loop-invariant
  %idx = add i32 %i, %c2      ; not invariant (depends on i)
  %val = load i32, ptr %A     ; not invariant (memory read)
  %i_next = add i32 %i, 1
  %cond = icmp slt i32 %i_next, %N
  br i1 %cond, label %loop, label %exit

exit:
  ret void
}
