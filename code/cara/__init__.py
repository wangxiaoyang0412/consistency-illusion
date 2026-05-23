"""
CARA (Cross-Agent Reasoning Alignment) metric pipeline.

exp-pilot-004: Computes CARA-HYB, CARA-SIM, and Contradiction Rate (CR)
on pilot traces from exp-pilot-003 (M3 + M4 on 50 MedThink-Bench questions).
"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# ^^ Required due to libiomp5md.dll conflict between conda MKL and torch 2.5.1+cu121.
# See exp-pilot-001b for root cause analysis.
import torch  # noqa: E402
