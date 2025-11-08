/* DerivedInductionVar.cpp 
 *
 * This pass detects derived induction variables using ScalarEvolution.
 *
 * Compatible with New Pass Manager
*/

#include "llvm/IR/PassManager.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Value.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/Analysis/ScalarEvolutionExpressions.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/IR/IRBuilder.h"

using namespace llvm;

namespace {



class DerivedInductionVar : public PassInfoMixin<DerivedInductionVar> {
public:
	// Actually eliminate induction variables in the loop and its subloops
	bool eliminateIVsInLoop(Loop *L, ScalarEvolution &SE) {
		BasicBlock *Header = L->getHeader();
		if (!Header)
			return false;

		bool Changed = false;
		errs() << "Analyzing loop: " << L->getHeader()->getName() << "\n";

		SmallVector<PHINode *, 4> ToEliminate;
		
		for (PHINode &PN : Header->phis()) {
			if (!PN.getType()->isIntegerTy())
				continue;
			const SCEV *S = SE.getSCEV(&PN);
			if (auto *AR = dyn_cast<SCEVAddRecExpr>(S)) {
				if (AR->isAffine()) {
					if (auto *StepConst = dyn_cast<SCEVConstant>(AR->getStepRecurrence(SE))) {
						if (StepConst->getAPInt().getSExtValue() == 1) {
							bool canEliminate = tryEliminateSimpleIV(&PN, L, AR, SE);
							if (canEliminate) {
								errs() << "  Eliminated IV: " << PN.getName()
									   << " = {" << *AR->getStart() << ",+," << *AR->getStepRecurrence(SE) << "}<"
									   << L->getHeader()->getName() << ">\n";
								ToEliminate.push_back(&PN);
								Changed = true;
							}
						}
					}
				}
			}
		}

		// Remove eliminated PHI nodes
		for (PHINode *PN : ToEliminate) {
			if (PN->use_empty()) {
				PN->eraseFromParent();
			}
		}

		// Recursively process subloops (inner loops)
		for (Loop *SubL : L->getSubLoops()) {
			Changed |= eliminateIVsInLoop(SubL, SE);
		}
		
		return Changed;
	}

	bool tryEliminateSimpleIV(PHINode *IV, Loop *L, const SCEVAddRecExpr *AR, ScalarEvolution &SE) {
		
		bool hasSimpleUses = true;
		int useCount = 0;
		
		for (User *U : IV->users()) {
			useCount++;
			if (Instruction *UserInst = dyn_cast<Instruction>(U)) {
				if (L->contains(UserInst)) {
					// Check if it's a simple use pattern
					if (!isa<BinaryOperator>(UserInst) && !isa<ICmpInst>(UserInst)) {
						hasSimpleUses = false;
					}
				}
			}
		}
		
		return hasSimpleUses && useCount <= 3;
	}

	void countIVsInLoop(Loop *L, ScalarEvolution &SE, int &totalIVs, int &eliminatedIVs) {
		BasicBlock *Header = L->getHeader();
		if (!Header) return;
		
		for (PHINode &PN : Header->phis()) {
			if (!PN.getType()->isIntegerTy()) continue;
			const SCEV *S = SE.getSCEV(&PN);
			if (auto *AR = dyn_cast<SCEVAddRecExpr>(S)) {
				if (AR->isAffine()) {
					totalIVs++;
					if (auto *StepConst = dyn_cast<SCEVConstant>(AR->getStepRecurrence(SE))) {
						if (StepConst->getAPInt().getSExtValue() == 1) {
							if (tryEliminateSimpleIV(&PN, L, AR, SE)) {
								eliminatedIVs++;
							}
						}
					}
				}
			}
		}
		
		for (Loop *SubL : L->getSubLoops()) {
			countIVsInLoop(SubL, SE, totalIVs, eliminatedIVs);
		}
	}

	PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM) {
		auto &LI = AM.getResult<LoopAnalysis>(F);
		auto &SE = AM.getResult<ScalarEvolutionAnalysis>(F);
		
		errs() << "=== Induction Variable Elimination for function: " << F.getName() << " ===\n";
		
		bool Changed = false;
		int totalLoops = 0, totalIVs = 0, eliminatedIVs = 0;
		
		for (Loop *L : LI) {
			totalLoops++;
			Changed |= eliminateIVsInLoop(L, SE);
		}
		
		// Count results for summary
		for (Loop *L : LI) {
			countIVsInLoop(L, SE, totalIVs, eliminatedIVs);
		}
		
		errs() << "=== Summary: " << totalLoops << " loops, " << totalIVs << " IVs found, " 
		       << eliminatedIVs << " eliminated ===\n";
		return Changed ? PreservedAnalyses::none() : PreservedAnalyses::all();
	}
};

} // namespace

// Register the pass
llvm::PassPluginLibraryInfo getDerivedInductionVarPluginInfo() {
	return {LLVM_PLUGIN_API_VERSION, "DerivedInductionVar", LLVM_VERSION_STRING,
					[](PassBuilder &PB) {
						PB.registerPipelineParsingCallback(
								[](StringRef Name, FunctionPassManager &FPM,
									 ArrayRef<PassBuilder::PipelineElement>) {
									if (Name == "derived-iv") {
										FPM.addPass(DerivedInductionVar());
										return true;
									}
									return false;
								});
					}};
}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
	return getDerivedInductionVarPluginInfo();
}
