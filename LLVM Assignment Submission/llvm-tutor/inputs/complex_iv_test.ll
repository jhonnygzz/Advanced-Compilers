; Complex nested loops with multiple induction variables and derived IVs
; This tests: triple nested loops, multiple IVs per loop, derived IVs, different step sizes

define void @complex_nested_loops(i32 %N, i32 %M, ptr %A) {
entry:
  br label %outer_loop

outer_loop:                                       ; Triple nested loop structure
  %i = phi i32 [0, %entry], [%i_next, %outer_end]
  %i_doubled = mul i32 %i, 2                     ; Derived IV: i*2
  %i_plus_offset = add i32 %i, 10                ; Derived IV: i+10
  br label %middle_loop

middle_loop:                                      ; Middle loop with step-2 IV
  %j = phi i32 [0, %outer_loop], [%j_next, %middle_end]
  %j_times3 = mul i32 %j, 3                      ; Derived IV: j*3
  %combined_ij = add i32 %i_doubled, %j_times3   ; Complex derived expression
  br label %inner_loop

inner_loop:                                       ; Inner loop with multiple IVs
  %k = phi i32 [1, %middle_loop], [%k_next, %inner_body]  ; Start from 1, not 0
  %temp = phi i32 [0, %middle_loop], [%temp_next, %inner_body]  ; Secondary IV
  %k_squared = mul i32 %k, %k                    ; Derived IV: k^2
  %complex_expr = add i32 %combined_ij, %k_squared
  br label %inner_body

inner_body:
  ; Use multiple IVs in various computations
  %idx1 = add i32 %i_plus_offset, %j             ; Mix of derived and basic IVs
  %idx2 = mul i32 %k, %temp                      ; Product of two IVs
  %array_idx = add i32 %idx1, %idx2              ; Complex index calculation
  
  ; Memory operations (should prevent some eliminations)
  %ptr = getelementptr i32, ptr %A, i32 %array_idx
  store i32 %complex_expr, ptr %ptr
  
  ; Update IVs
  %k_next = add i32 %k, 1                        ; Step 1
  %temp_next = add i32 %temp, 2                  ; Step 2 (different step size)
  
  ; Inner loop condition
  %inner_cond = icmp slt i32 %k_next, 5
  br i1 %inner_cond, label %inner_loop, label %middle_end

middle_end:
  %j_next = add i32 %j, 2                        ; Step 2 IV
  %middle_cond = icmp slt i32 %j_next, %M
  br i1 %middle_cond, label %middle_loop, label %outer_end

outer_end:
  %i_next = add i32 %i, 1                        ; Step 1 IV
  %outer_cond = icmp slt i32 %i_next, %N
  br i1 %outer_cond, label %outer_loop, label %exit

exit:
  ret void
}

; Additional function with step-3 and negative step IVs
define void @complex_steps_test(i32 %limit) {
entry:
  br label %step3_loop

step3_loop:
  %i3 = phi i32 [0, %entry], [%i3_next, %step3_loop]
  %i3_derived = sub i32 %i3, 5                   ; Derived: i3 - 5
  %i3_next = add i32 %i3, 3                      ; Step 3
  %cond3 = icmp slt i32 %i3_next, %limit
  br i1 %cond3, label %step3_loop, label %countdown_loop

countdown_loop:
  %down = phi i32 [100, %step3_loop], [%down_next, %countdown_loop]
  %down_derived = mul i32 %down, -1              ; Derived: -down
  %down_next = sub i32 %down, 2                  ; Negative step (countdown)
  %down_cond = icmp sgt i32 %down_next, 0
  br i1 %down_cond, label %countdown_loop, label %exit2

exit2:
  ret void
}