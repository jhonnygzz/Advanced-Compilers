For this assignment, we were tasked on adding four additional functions to our cfg.py file. Each function would take the cfg  and return an output varies by the user. I will be describing each function along with the different test cases I have chosen for this assignment. 

Get Path Lengths
For this function, it computes the shortest path using the edges from a specific entry block that we pass as a string using the reachable blocks from the entry block in the CFG. It helps us determine the length at which each block is from the entry block.  


Reverse Post Order
For this function, it will return the nodes of the CFG in the reverse postorder. This is a common traversal technique used in compiler analysis. Here the nodes are visited after their successors, which at the end the list order is reversed. It helps understand the natural execution flow of the program. 

Find Back Edges
Here the function will find all back edges in the cfg. A back edge is an edge that informs there is a loop by noting that the edge points to one of the node's prior blocks. This helps with loop analysis and optimizations. 

Is Reducible
Here, the function checks whether the cfg is reducible. It has a few requirements, which involve ensuring that the loops in the cfg only have a single entry point. It uses the back edges and reachability to determine whether the conditions are met. 

I went over the bril directory and found two suitable bril files that I chose as my test cases. I chose fact.bril and gcd.bril. As the entry point, I put b0 and the output produced from my cfg.py file can be found as fact.out and gcd.out. 