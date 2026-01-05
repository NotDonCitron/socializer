# Priority Fixes Implementation Plan

## Core Priority Fixes
- [ ] Priority 1: Fix semver_major_bump logic bug in radar/pipeline/score.py
- [ ] Priority 2: Fix storage schema alignment in radar/storage.py
- [ ] Priority 3: Fix LLM issues (MockLLM string and GeminiLLM client attribute)
- [ ] Priority 4: Add kind field to GeneratedPost in radar/models.py
- [ ] Priority 5: Fix render weekly path alignment in radar/pipeline/generate.py
- [ ] Priority 6: Allow NULL title in RawItem for edge cases

## Testing & Validation
- [ ] Run test_pipeline_score.py to verify Priority 1
- [ ] Run test_storage.py to verify Priority 2
- [ ] Run test_llm.py to verify Priority 3
- [ ] Run test_pipeline_generate.py and test_pipeline_other.py to verify Priority 5
- [ ] Run test_edge_cases.py to verify Priority 6

## Follow-up Priorities
- [ ] Priority 7: Investigate CLI test failures
- [ ] Priority 8: Fix Playwright test flakiness

## Implementation Order
1. Apply Priority 1-6 fixes systematically
2. Run tests to verify each fix
3. Address any test failures
4. Plan follow-up for Priorities 7-8