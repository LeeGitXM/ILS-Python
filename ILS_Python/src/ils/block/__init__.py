# Define the modules that are executable block classes
# This is required for "from ils.block import *" to give the desired answer
#
# **** ALL NAMES MUST BE ALL LOWER CASE OR IT WILL FAIL ****
#
__all__ = ["action","arithmetic","finaldiagnosis","sqcdiagnosis","subdiagnosis"]