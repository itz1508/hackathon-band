# Complete Workflow for Agent Skills Framework

## Executive Summary

The Agent Skills Framework is a **deterministic, auditable system** for managing agent execution through a **10-stage warranty cycle** with strict **role boundaries, quality gates, and proof verification**.

The workflow ensures:
- ✅ **One-shot execution** without breaks or loops
- ✅ **Quality guarantee** (93.91% threshold before simulation)
- ✅ **Proof of execution** (immutable audit trail)
- ✅ **Role-bound workers** (explicit permissions and boundaries)
- ✅ **Plan-Validate-Execute** (no auto-rewriting)

---

## Phase 1: Task Submission & Planning

### 1.1 User Submits Task

```
User
  ├─ Provides task description
  ├─ Specifies repository/scope
  ├─ Defines success criteria
  └─ Sets constraints
```

**Input:**
- Task ID
- Repository path
- Success criteria
- Constraints (time, resources, scope)

**Output:**
- Task configuration
- Initial context

---

### 1.2 Broker/Router Agent Receives Task

**Responsibility:** Route task to appropriate agents

```
BrokerAgent
  ├─ Receives task configuration
  ├─ Analyzes task complexity
  ├─ Determines workflow type (one-shot, iterative, etc.)
  ├─ Creates execution plan
  └─ Routes to Scan Worker
```

**Actions:**
1. Parse task configuration
2. Analyze requirements
3. Create execution plan
4. Initialize execution context

**Output:**
- Execution plan
- Task routing decision
- Initial context

---

## Phase 2: Source of Truth Establishment

### 2.1 Scan Worker (Stage 01)

**Role:** Analyze task and establish source of truth

```
ScanWorker
  ├─ Enumerate files in scope
  ├─ Hash all files (immutable snapshot)
  ├─ Analyze dependencies
  ├─ Create scope definition
  └─ Generate initial context
```

**Allowed Actions:**
- ✅ Read files
- ✅ Enumerate directories
- ✅ Hash files
- ✅ Analyze structure

**Forbidden Actions:**
- ❌ Modify files
- ❌ Delete files
- ❌ Execute commands

**Output:**
- File snapshot (hashes)
- Scope definition (allowed files)
- Dependency analysis
- Initial context

---

### 2.2 Raw Statement Skill (Stage 02)

**Role:** Generate raw analysis from scan results

```
RawStatementSkill
  ├─ Receives scan results
  ├─ Analyzes findings
  ├─ Generates raw statement
  ├─ Documents analysis process
  └─ Creates proof of analysis
```

**Input Requirements:**
- Scan results
- File snapshot
- Scope definition

**Output:**
- Raw statement (analysis)
- Proof of analysis
- Findings list

**Proof Requirements:**
- Must reference scan results
- Must document methodology
- Must be reproducible

---

### 2.3 Handoff Statement Skill (Stage 03)

**Role:** Prepare for external processing

```
HandoffStatementSkill
  ├─ Receives raw statement
  ├─ Validates completeness
  ├─ Prepares for handoff
  ├─ Creates handoff proof
  └─ Marks ready for processing
```

**Input Requirements:**
- Raw statement (from Stage 02)
- Scope definition
- File snapshot

**Output:**
- Handoff statement
- Handoff proof
- Ready flag

**Proof Requirements:**
- Must reference raw statement
- Must validate dependencies
- Must be deterministic

---

### 2.4 LLM Statement Skill (Stage 04)

**Role:** Get LLM synthesis

```
LLMStatementSkill
  ├─ Receives raw + handoff statements
  ├─ Calls LLM for synthesis
  ├─ Documents LLM response
  ├─ Creates synthesis proof
  └─ Validates output
```

**Input Requirements:**
- Raw statement (from Stage 02)
- Handoff statement (from Stage 03)
- LLM model specification

**Output:**
- LLM statement (synthesis)
- LLM proof (model, prompt, response)
- Synthesis result

**Proof Requirements:**
- Must reference raw + handoff
- Must include LLM metadata
- Must be reproducible

---

## Phase 3: Pre-Simulation Quality Gate

### 3.1 Source of Truth Validation

**Role:** Validate all statements exist and are complete

```
SourceOfTruthValidator
  ├─ Verify raw statement exists
  ├─ Verify handoff statement exists
  ├─ Verify LLM statement exists
  ├─ Verify scope definition
  ├─ Verify all proofs present
  └─ Create source of truth
```

**Validation Checks:**
- ✅ All statements present
- ✅ All proofs present
- ✅ All references valid
- ✅ Scope complete
- ✅ No contradictions

**Output:**
- Source of Truth object
- Validation report

---

### 3.2 Pre-Simulation Package Creation

**Role:** Create proposed plan/package

```
PackageBuilder
  ├─ Receives source of truth
  ├─ Creates package structure
  ├─ Defines scope boundaries
  ├─ Lists forbidden actions
  ├─ Specifies requirements
  └─ Creates pre-simulation package
```

**Package Contents:**
- Components (tasks to execute)
- Scope definition (allowed files)
- Forbidden actions (delete, truncate, etc.)
- Requirements mapping
- Constraints

**Output:**
- Pre-Simulation Package
- Package metadata

---

### 3.3 Qualification Validation (Plan-Validate-Execute)

**Role:** Validate package against source of truth

```
QualificationValidator
  ├─ Check all requirements mapped
  ├─ Check all components valid
  ├─ Check all references valid
  ├─ Check scope compliance
  ├─ Check forbidden actions
  └─ Generate gap report
```

**Validation Logic:**
1. **Requirement Satisfaction** — All mandatory requirements mapped
2. **Component Validity** — All components exist and are complete
3. **Reference Proof** — All components reference source of truth
4. **Scope Compliance** — Allowed files match scope (normalized paths)
5. **Forbidden Actions** — All destructive operations blocked

**Output:**
- Qualification Status (QUALIFIED or NOT_QUALIFIED)
- Gap Report (if NOT_QUALIFIED)
  - Concrete missing items only
  - No inventing or auto-fixing
  - Severity levels (critical/high/medium/low)

**Decision:**
- ✅ QUALIFIED → Proceed to Simulation
- ❌ NOT_QUALIFIED → Return gap report to user/agent for fixes

---

## Phase 4: Simulation (Only if Qualified)

### 4.1 Simulation Sandbox Setup

**Role:** Create isolated execution environment

```
SimulationSandbox
  ├─ Create isolated environment
  ├─ Copy allowed files only
  ├─ Set up file watchers
  ├─ Initialize logging
  └─ Create rollback point
```

**Setup:**
- Isolated filesystem
- File change tracking
- Execution logging
- Rollback capability

**Output:**
- Sandbox environment
- Rollback point ID

---

### 4.2 10-Stage Warranty Cycle Execution

#### Stage 1: Scan
```
ScanWorker.execute()
  ├─ Enumerate files
  ├─ Hash files
  ├─ Analyze dependencies
  └─ Create snapshot
```

#### Stage 2: Raw Statement
```
RawStatementSkill.execute()
  ├─ Analyze scan results
  ├─ Generate analysis
  ├─ Create proof
  └─ Document findings
```

#### Stage 3: Handoff
```
HandoffStatementSkill.execute()
  ├─ Validate raw statement
  ├─ Prepare for processing
  ├─ Create handoff proof
  └─ Mark ready
```

#### Stage 4: LLM Statement
```
LLMStatementSkill.execute()
  ├─ Call LLM
  ├─ Get synthesis
  ├─ Create proof
  └─ Validate output
```

#### Stage 5: Evaluation
```
EvaluationWorker.execute()
  ├─ Run tests
  ├─ Track test count
  ├─ Capture output
  ├─ Update verification state
  └─ Return test results
```

**Real Command Execution:**
```python
result = subprocess.run(
    ["pytest", "..."],
    capture_output=True,
    text=True
)
# Track: exit_code, stdout, stderr, test_count
```

#### Stage 6: Warranty Check
```
WarrantyCheckWorker.execute()
  ├─ Calculate confidence %
  ├─ Check against 93.91% threshold
  ├─ Create warranty proof
  └─ Decide: proceed or retry
```

**Confidence Calculation:**
- Base: 85% (if tests pass)
- +5% if test count > 500
- +5% if no stderr

**Decision:**
- ✅ >= 93.91% → Proceed to Final Result
- ❌ < 93.91% → Go to Retry Logic

#### Stage 7: Retry Logic
```
RetryLogicWorker.execute()
  ├─ Analyze failures
  ├─ Suggest improvements
  ├─ Apply fixes
  └─ Decide: retry or fail
```

#### Stage 8: Final Result
```
FinalResultWorker.execute()
  ├─ Generate final output
  ├─ Summarize results
  ├─ Create final proof
  └─ Prepare for locking
```

#### Stage 9: Lock Result
```
LockResultWorker.execute()
  ├─ Lock execution proof
  ├─ Make immutable
  ├─ Create audit trail
  └─ Prepare for cleanup
```

**Locked Proof Contains:**
- Final state (all artifacts)
- Execution log (all events)
- Timestamp (when locked)
- Immutable flag (cannot modify)

#### Stage 10: Cleanup
```
CleanupWorker.execute()
  ├─ Save snapshot
  ├─ Save audit log
  ├─ Reset state
  ├─ Close sandbox
  └─ Return final state
```

**Persistent Storage:**
```python
snapshot = ExecutionSnapshot(
    snapshot_id=...,
    task_id=...,
    execution_state=final_state,
    execution_log=log,
    metadata={...}
)
storage_manager.save_snapshot(snapshot)
storage_manager.save_log_entry(audit_entry)
```

---

### 4.3 Stop Condition Checking

**When to Stop:**
- ✅ After full test suite passes
- ✅ After warranty check passes (>= 93.91%)
- ✅ After final result generated
- ✅ After cleanup completes

**Stop Logic:**
```
for phase in [SCAN, RAW, HANDOFF, LLM, EVAL, WARRANTY, RETRY, FINAL, LOCK, CLEANUP]:
    execute_phase(phase)
    
    # Only check stop AFTER finalization phases
    if phase >= FINAL_RESULT:
        if should_stop():
            break
    
    # Always execute CLEANUP
    if phase == CLEANUP:
        break
```

---

## Phase 5: Verification & Proof

### 5.1 Replay Verification

**Role:** Verify execution is reproducible

```
ReplayVerifier
  ├─ Load execution snapshot
  ├─ Replay all stages
  ├─ Compare outputs
  ├─ Verify determinism
  └─ Create replay proof
```

**Verification:**
- Execute same steps
- Compare results
- Verify determinism
- Create proof

**Output:**
- Replay proof
- Determinism verification
- Reproducibility status

---

### 5.2 Authority Review

**Role:** Human/authority reviews and approves

```
AuthorityReviewer
  ├─ Reviews execution proof
  ├─ Reviews locked state
  ├─ Reviews audit trail
  ├─ Makes approval decision
  └─ Creates approval proof
```

**Review Checklist:**
- ✅ Execution proof valid
- ✅ All stages completed
- ✅ Quality threshold met
- ✅ No unauthorized changes
- ✅ Audit trail complete

**Decision:**
- ✅ APPROVE → Proceed to Apply
- ❌ REJECT → Return to user with feedback

---

## Phase 6: Application & Deployment

### 6.1 Apply Boundary Enforcement

**Role:** Ensure only approved changes applied

```
ApplyBoundaryEnforcer
  ├─ Load approved changes
  ├─ Verify against approval
  ├─ Check scope boundaries
  ├─ Verify no extra changes
  └─ Mark ready for apply
```

**Enforcement:**
- Only apply approved changes
- Verify scope compliance
- Check file boundaries
- Prevent unauthorized modifications

**Output:**
- Apply boundary proof
- Ready for apply flag

---

### 6.2 User Apply

**Role:** User manually applies changes

```
UserApplyStep
  ├─ Present changes to user
  ├─ Show diff view
  ├─ Get user confirmation
  ├─ User applies changes
  └─ Create apply proof
```

**User Actions:**
1. Review changes
2. Review diffs
3. Confirm approval
4. Apply changes
5. Verify success

**Output:**
- Apply proof
- Change confirmation
- Success status

---

### 6.3 Verification After Apply

**Role:** Verify changes applied correctly

```
PostApplyVerifier
  ├─ Verify files changed
  ├─ Verify scope respected
  ├─ Verify no extra changes
  ├─ Run validation tests
  └─ Create verification proof
```

**Verification:**
- Files match approved changes
- No unauthorized modifications
- Scope boundaries respected
- Validation tests pass

**Output:**
- Verification proof
- Status report

---

## Phase 7: Reporting & Handoff

### 7.1 Report Generation

**Role:** Generate comprehensive report

```
ReportGenerator
  ├─ Collect all proofs
  ├─ Summarize execution
  ├─ Create diffs
  ├─ Generate report
  └─ Export in multiple formats
```

**Report Contents:**
- Executive summary
- Quality score
- Changes made
- Diffs (code changes)
- Audit trail
- Proofs
- Recommendations

**Output:**
- Full HTML report
- JSON schema export
- Summary report

---

### 7.2 LLM Analysis & Summary

**Role:** Intelligent analysis of results

```
LLMAnalyzer
  ├─ Analyze execution results
  ├─ Identify remaining issues
  ├─ Explain why issues remain
  ├─ Specify missing resources
  ├─ Provide next steps
  └─ Create summary
```

**Analysis:**
- What was accomplished
- What issues remain
- Why issues can't be resolved
- What's missing (tools, data, permissions)
- Next steps for success

**Output:**
- LLM analysis
- Summary report
- Recommendations

---

### 7.3 Dry Test Package

**Role:** Allow user to test before applying

```
DryTestGenerator
  ├─ Create test environment
  ├─ Copy changes to test env
  ├─ Create test scripts
  ├─ Document test procedure
  └─ Generate test package
```

**Test Package:**
- Test environment setup
- Test scripts
- Expected results
- Validation checklist

**Output:**
- Dry test package
- Test documentation

---

## Phase 8: Handoff to Other Agents

### 8.1 Isolation Report (If Failed)

**Role:** Analyze failures for other agents

```
IsolationEngine
  ├─ Identify failure point
  ├─ Analyze root cause
  ├─ Create isolation report
  ├─ Specify what's missing
  └─ Create handoff package
```

**Isolation Report:**
- Failed stage
- Root cause
- Error details
- What's missing
- Suggested fixes

**Output:**
- Isolation report
- Handoff package for fix agent

---

### 8.2 Handoff Package Creation

**Role:** Prepare work for other agents

```
HandoffPackageCreator
  ├─ Collect all artifacts
  ├─ Create specification
  ├─ Document requirements
  ├─ Create implementation guide
  └─ Generate handoff package
```

**Handoff Package:**
- Problem specification
- Requirements
- Implementation guide
- Code templates
- Test specifications
- Success criteria

**Output:**
- Handoff package (ZIP)
- Specification document
- Implementation guide

---

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT SKILLS FRAMEWORK                       │
│                   Complete Workflow (10 Stages)                 │
└─────────────────────────────────────────────────────────────────┘

PHASE 1: TASK SUBMISSION & PLANNING
  ↓
  User Submits Task
  ↓
  Broker/Router Agent Routes Task
  ↓

PHASE 2: SOURCE OF TRUTH ESTABLISHMENT
  ↓
  Stage 01: Scan Worker
  ├─ Enumerate files, create snapshot
  ↓
  Stage 02: Raw Statement Skill
  ├─ Analyze scan, generate analysis
  ↓
  Stage 03: Handoff Statement Skill
  ├─ Prepare for processing
  ↓
  Stage 04: LLM Statement Skill
  ├─ Get LLM synthesis
  ↓

PHASE 3: PRE-SIMULATION QUALITY GATE
  ↓
  Source of Truth Validation
  ├─ Verify all statements exist
  ↓
  Pre-Simulation Package Creation
  ├─ Create proposed plan
  ↓
  Qualification Validation (PLAN-VALIDATE-EXECUTE)
  ├─ Validate package against truth
  ├─ If NOT QUALIFIED → Return gap report (NO AUTO-FIX)
  └─ If QUALIFIED → Proceed to simulation
  ↓

PHASE 4: SIMULATION (Only if Qualified)
  ↓
  Simulation Sandbox Setup
  ├─ Create isolated environment
  ↓
  10-Stage Warranty Cycle:
  ├─ Stage 05: Evaluation (Run tests, track results)
  ├─ Stage 06: Warranty Check (Calculate confidence)
  ├─ Stage 07: Retry Logic (If < 93.91%)
  ├─ Stage 08: Final Result (Generate output)
  ├─ Stage 09: Lock Result (Make immutable)
  └─ Stage 10: Cleanup (Save snapshots, audit logs)
  ↓
  Stop Condition Check
  ├─ Only after finalization phases
  └─ Always complete cleanup
  ↓

PHASE 5: VERIFICATION & PROOF
  ↓
  Replay Verification
  ├─ Verify reproducibility
  ↓
  Authority Review
  ├─ Human/authority approval
  ├─ If REJECTED → Return to user
  └─ If APPROVED → Proceed to apply
  ↓

PHASE 6: APPLICATION & DEPLOYMENT
  ↓
  Apply Boundary Enforcement
  ├─ Verify scope compliance
  ↓
  User Apply
  ├─ User reviews and applies changes
  ↓
  Post-Apply Verification
  ├─ Verify changes applied correctly
  ↓

PHASE 7: REPORTING & HANDOFF
  ↓
  Report Generation
  ├─ Create comprehensive report
  ├─ HTML diffs
  └─ JSON schema export
  ↓
  LLM Analysis & Summary
  ├─ Analyze results
  ├─ Explain remaining issues
  ├─ Specify missing resources
  └─ Provide next steps
  ↓
  Dry Test Package
  ├─ Allow user to test before applying
  ↓

PHASE 8: HANDOFF TO OTHER AGENTS (If Needed)
  ↓
  Isolation Report (If Failed)
  ├─ Analyze failures
  ├─ Identify root cause
  └─ Create handoff package
  ↓
  Handoff Package Creation
  ├─ Prepare work for other agents
  ├─ Include specification
  ├─ Include requirements
  └─ Include implementation guide
  ↓

END: COMPLETE WORKFLOW
```

---

## Key Principles

### 1. Deterministic Execution
- Same input → Same output
- Replay verification proves determinism
- Immutable audit trail

### 2. Quality Guarantee
- 93.91% threshold before simulation
- No execution without qualification
- Concrete gap reports (no inventing)

### 3. Proof-Based System
- Every stage creates proof
- Proofs reference source of truth
- Locked proof is immutable

### 4. Role-Bound Workers
- Explicit permissions (allowed actions)
- Explicit restrictions (forbidden actions)
- Clear boundaries

### 5. Plan-Validate-Execute
- Create plan (package)
- Validate against truth
- Execute only if qualified
- NO auto-rewriting

### 6. One-Shot Execution
- No infinite loops
- No breaks in workflow
- All 10 stages complete
- Stop conditions checked only after finalization

### 7. Audit Trail
- Every action logged
- Every decision documented
- Immutable proof trail
- Reproducible execution

---

## Success Criteria

✅ **Workflow Complete** — All 10 stages executed  
✅ **Quality Threshold Met** — >= 93.91% confidence  
✅ **Proof Verified** — Replay verification passed  
✅ **Authority Approved** — Human/authority sign-off  
✅ **Changes Applied** — User applied changes  
✅ **Verification Passed** — Post-apply verification successful  
✅ **Report Generated** — Comprehensive report created  
✅ **Audit Trail Complete** — Full execution logged  

---

## Error Handling

### If Qualification Fails
- Return concrete gap report
- NO auto-rewriting
- User/agent fixes gaps
- Resubmit for validation

### If Simulation Fails
- Create isolation report
- Identify root cause
- Create handoff package
- Route to fix agent

### If Verification Fails
- Return to user with details
- Suggest next steps
- Create dry test package
- Allow user to retry

---

## Integration Points

1. **Real Agent Execution** — Replace simulated LLM calls
2. **Persistent Storage** — Snapshots and audit logs
3. **Multi-Agent Orchestration** — Manager agent coordination
4. **External APIs** — LLM, storage, notification services
5. **Monitoring & Analytics** — Track execution metrics

---

This complete workflow ensures **deterministic, auditable, one-shot execution** with strict **quality guarantees** and **proof verification** at every stage.
