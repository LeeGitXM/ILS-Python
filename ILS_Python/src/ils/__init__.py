# Define the modules that are executable block classes, including BasicBlock
# This is required for "from emc.block import *" to give the desired answer
__all__ = ["basicblock","action","arithmetic","finaldiagnosis","sqcdiagnosis","subdiagnosis"]
