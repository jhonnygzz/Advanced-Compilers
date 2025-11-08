; Edge cases and complex scenarios for IVE testing
define void @edge_cases_test(i32 %N, ptr %array) {
entry:
  br label %simple_eliminable

; Simple case that should be eliminable
simple_eliminable:
  %simple_i = phi i32 [0, %entry], [%simple_next, %simple_eliminable]
  %simple_use = add i32 %simple_i, 1              ; Simple arithmetic use
  %simple_next = add i32 %simple_i, 1
  %simple_cond = icmp slt i32 %simple_next, 3
  br i1 %simple_cond, label %simple_eliminable, label %complex_uses

; Complex uses that should NOT be eliminable  
complex_uses:
  %complex_i = phi i32 [0, %simple_eliminable], [%complex_next, %complex_uses]
  %ptr_use = getelementptr i32, ptr %array, i32 %complex_i    ; GEP use (complex)
  %loaded = load i32, ptr %ptr_use                            ; Memory operation
  %call_use = call i32 @external_func(i32 %complex_i)         ; Function call (complex)
  %complex_next = add i32 %complex_i, 1
  %complex_cond = icmp slt i32 %complex_next, 5
  br i1 %complex_cond, label %complex_uses, label %mixed_loop

; Mixed scenario: some eliminable, some not
mixed_loop:
  %mix_i = phi i32 [0, %complex_uses], [%mix_i_next, %mixed_loop]
  %mix_j = phi i32 [10, %complex_uses], [%mix_j_next, %mixed_loop]
  %eliminable_use = mul i32 %mix_i, 2              ; Simple use - eliminable
  %complex_use = getelementptr i32, ptr %array, i32 %mix_j  ; Complex use - not eliminable
  %mix_i_next = add i32 %mix_i, 1
  %mix_j_next = add i32 %mix_j, 1  
  %mix_cond = icmp slt i32 %mix_i_next, 8
  br i1 %mix_cond, label %mixed_loop, label %quadruply_nested

; Quadruple nested loops (extreme nesting)
quadruply_nested:
  %a = phi i32 [0, %mixed_loop], [%a_next, %level1_end]
  br label %level1

level1:
  %b = phi i32 [0, %quadruply_nested], [%b_next, %level2_end]  
  %ab_product = mul i32 %a, %b                     ; Cross-loop derived IV
  br label %level2

level2:
  %c = phi i32 [0, %level1], [%c_next, %level3_end]
  %abc_sum = add i32 %ab_product, %c               ; Multi-level derived IV
  br label %level3

level3:
  %d = phi i32 [0, %level2], [%d_next, %level3]
  %abcd_complex = mul i32 %abc_sum, %d             ; Very complex derived expression
  %d_next = add i32 %d, 1
  %level3_cond = icmp slt i32 %d_next, 2
  br i1 %level3_cond, label %level3, label %level3_end

level3_end:
  %c_next = add i32 %c, 1
  %level2_cond = icmp slt i32 %c_next, 3
  br i1 %level2_cond, label %level2, label %level2_end

level2_end:
  %b_next = add i32 %b, 1
  %level1_cond = icmp slt i32 %b_next, 4
  br i1 %level1_cond, label %level1, label %level1_end

level1_end:
  %a_next = add i32 %a, 1
  %level0_cond = icmp slt i32 %a_next, 5
  br i1 %level0_cond, label %quadruply_nested, label %exit

exit:
  ret void
}

; External function declaration for testing complex uses
declare i32 @external_func(i32)

; Function with only simple, eliminable IVs
define void @all_eliminable_test() {
entry:
  br label %loop1

loop1:
  %i1 = phi i32 [0, %entry], [%i1_next, %loop1]
  %simple1 = add i32 %i1, 5                       ; Simple arithmetic
  %i1_next = add i32 %i1, 1
  %cond1 = icmp slt i32 %i1_next, 3
  br i1 %cond1, label %loop1, label %loop2

loop2:
  %i2 = phi i32 [0, %loop1], [%i2_next, %loop2]
  %simple2 = sub i32 %i2, 2                       ; Simple arithmetic
  %cmp_use = icmp eq i32 %i2, 1                   ; Simple comparison
  %i2_next = add i32 %i2, 1
  %cond2 = icmp slt i32 %i2_next, 4
  br i1 %cond2, label %loop2, label %exit2

exit2:
  ret void
}