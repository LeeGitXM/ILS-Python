# Define the modules that are executable block classes
# This is required for "from emc.block import *" to give the desired answer
__all__ = ["action","arithmetic","finaldiagnosis","sqcdiagnosis","subdiagnosis"]