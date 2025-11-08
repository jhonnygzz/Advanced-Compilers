
/* SimpleLICM.cpp
 *
 * This pass hoists loop-invariant code before the loop when it is safe to do so.
 *
 * Compatible with New Pass Manage
*/

#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/Dominators.h"
#include "llvm/IR/CFG.h"

#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

#include "llvm/Analysis/LoopAnalysisManager.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/LoopPass.h"
#include "llvm/Analysis/TargetLibraryInfo.h"
#include "llvm/Analysis/ValueTracking.h"

#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/Transforms/Utils/LoopUtils.h"
#include "llvm/Transforms/Utils/ValueMapper.h"

using namespace llvm;

struct SimpleLICM : public PassInfoMixin<SimpleLICM> {
	PreservedAnalyses run(Loop &L, LoopAnalysisManager &AM,
												LoopStandardAnalysisResults &AR,
												LPMUpdater &) {
		DominatorTree &DT = AR.DT;

		BasicBlock *Preheader = L.getLoopPreheader();
		if (!Preheader) {
			errs() << "No preheader, skipping loop\n";
			return PreservedAnalyses::all();
		}

		SmallPtrSet<Instruction *, 8> InvariantSet;
		bool Change = true;


			// Worklist algorithm to identify loop invariant instructions
			SmallVector<Instruction *, 32> WorkList;
			SmallPtrSet<Instruction *, 32> Visited;


			for (auto *BB : L.blocks()) {
				for (auto &I : *BB) {

					if (isa<PHINode>(&I)) continue;
					if (I.mayReadOrWriteMemory()) continue;
					bool AllInvariant = true;
					for (unsigned op = 0; op < I.getNumOperands(); ++op) {
						Value *Op = I.getOperand(op);
						if (Instruction *OpInst = dyn_cast<Instruction>(Op)) {
							if (L.contains(OpInst->getParent())) {
								AllInvariant = false;
								break;
							}
						}
					}
					if (AllInvariant) {
						WorkList.push_back(&I);
						InvariantSet.insert(&I);
					}
				}
			}

			bool Changed = true;
			while (Changed) {
				Changed = false;
				for (auto *BB : L.blocks()) {
					for (auto &I : *BB) {
						if (isa<PHINode>(&I)) continue;
						if (I.mayReadOrWriteMemory()) continue;
						if (InvariantSet.contains(&I)) continue;
						bool AllInvariant = true;
						for (unsigned op = 0; op < I.getNumOperands(); ++op) {
							Value *Op = I.getOperand(op);
							if (Instruction *OpInst = dyn_cast<Instruction>(Op)) {
								if (L.contains(OpInst->getParent()) && !InvariantSet.contains(OpInst)) {
									AllInvariant = false;
									break;
								}
							}
						}
						if (AllInvariant) {
							WorkList.push_back(&I);
							InvariantSet.insert(&I);
							Changed = true;
						}
					}
				}
			}

		for (Instruction *I : InvariantSet) {
			if (isSafeToSpeculativelyExecute(I) && dominatesAllLoopExits(I, &L, DT)) {
				errs() << "Hoisting: " << *I << "\n";
				I->moveBefore(Preheader->getTerminator());
			}
		}

		return PreservedAnalyses::none();
	}

	bool dominatesAllLoopExits(Instruction *I, Loop *L, DominatorTree &DT) {
		SmallVector<BasicBlock *, 8> ExitBlocks;
		L->getExitBlocks(ExitBlocks);
		for (BasicBlock *EB : ExitBlocks) {
			if (!DT.dominates(I, EB))
				return false;
		}
		return true;
	}
};

llvm::PassPluginLibraryInfo getSimpleLICMPluginInfo() {
	errs() << "SimpleLICM plugin: getSimpleLICMPluginInfo() called\n";
	return {LLVM_PLUGIN_API_VERSION, "simple-licm", LLVM_VERSION_STRING,
					[](PassBuilder &PB) {
						PB.registerPipelineParsingCallback(
								[](StringRef Name, LoopPassManager &LPM,
									 ArrayRef<PassBuilder::PipelineElement>) {
									if (Name == "simple-licm") {
										LPM.addPass(SimpleLICM());
										return true;
									}                  
									return false;
								});
					}};
}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
	errs() << "SimpleLICM plugin: llvmGetPassPluginInfo() called\n";
	return getSimpleLICMPluginInfo();
}
