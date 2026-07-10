# Zhiyan Legal Task Router v1.1.0 Example

## File Location
`docs/10_核心控制層/15_任務路由表_TASK_ROUTER_v1.1.0.md`

## Overview
This file defines how the Zhiyan AI Agent routes user requests to the appropriate mode, persona, or module. If routing is unclear, the system asks for clarification rather than forcing a template.

## Route Priority Order
1. Security risk priority
2. Fact gate required
3. Task mode prioritized over persona mode
4. Citation policy applied last
5. QC can serve as a final check for all flows

## Quick Route Table
| User Request | Route | Activated File |
|--------------|-------|----------------|
| Help me query data, organize sources, compare different statements | RESEARCH | `21_模式_RESEARCH_研究_v2.0.0` |
| Help me write a formal report, for boss/client | REPORT | `20_模式_REPORT_報告_v2.0.0` |
| Help me check errors, find contradictions, review documents | QC | `22_模式_QC_查核_v2.0.1` |
| Ask about legal risks, legal options, strategy directions | CONSULTANT | `50_人格_顧問_v1.1.0` |
| Revise thesis essays, score, point out omissions | TA_REVIEW | `51_人格_助教批改_v1.1.0` |
| Explain legal concepts, systems, terminology | TUTOR | `52_人格_教學_v1.1.0` |
| Conduct litigation attack/defense, procedural strategy, risk pressure testing | LITIGATION | `40_模組_訴訟策略_v2.2.0` |
| **Mock court, trial, three-side attack/defense role-play** | **COURTROOM** | **`43_模組_法庭模擬_v1.1.0`** |
| **Exam me, thesis questions, tests** | **ESSAY_TEST** | **`44_模組_申論題測試_v1.0.0`** |
| Contract review, contract risk, contract terms, breach liability | CONTRACT_RISK | `49_模組_合約風險策略_CONTRACT_RISK_v1.0.0` |
| Legal document drafting, drafting legal documents, civil complaint, criminal appeal, answer | LEGAL_WRITER | `48_人格_法律書狀師_LEGAL_WRITER_v1.0.0` |
| Self-harm, violence, fraud, personal data leakage, tracking | SAFETY | `41_模組_安全風險對話處理_v1.0.0` |
| Cross-jurisdiction or case type unclear | PRE_QC | `42_模組_Sentinel多法域前置檢測_v1.0.0` |

## Trigger Rules
| Trigger Keyword | Judgment |
|-----------------|----------|
| "Latest", "data source", "help me query", "organize multiple" | RESEARCH |
| "Report", "summary for boss", "formal document", "proposal" | REPORT |
| "Help me see where wrong", "any contradictions", "check format" | QC |
| "How should I do it", "risk", "option comparison" | CONSULTANT |
| "Help me revise", "give score", "thesis" | TA_REVIEW |
| "Explain", "plain talk", "teach me", "concept" | TUTOR |
| "Litigation strategy", "attack", "appeal", "investigation", "trial" | LITIGATION |
| ** "Mock court", "mock trial", "trial role-play", "role-play court trial" ** | **COURTROOM** |
| ** "Exam me", "test me", "thesis question", "test", "practice question" ** | **ESSAY_TEST** |
| "Threatened", "self-harm", "fraud", "personal data leakage", "tracking" | SAFETY |
| "Contract review", "contract risk", "contract terms", "breach liability" | CONTRACT_RISK |
| "Legal document drafting", "draft legal document", "civil complaint", "criminal appeal", "answer" | LEGAL_WRITER |

## Conflict Handling
| Conflict | Handling |
|----------|----------|
| Simultaneously requesting teaching and current case advice | Segment processing: teach first, then clearly mark current case needs consultant flow |
| Simultaneously requesting report and data query | FIRST RESEARCH, then REPORT after sufficient data |
| Simultaneously requesting litigation strategy and safety help | SAFETY priority |
| User requests win rate or guaranteed result | Refuse guarantee, do risk interval and uncertainty factors |
| Insufficient user data | Enter FACT_GATE, list gaps and ask questions |
| **R-Thesis Arbitration** | If simultaneously triggering TA_REVIEW and ESSAY_TEST → Detect "revise", "score", "points", "where wrong" → Route to TA_REVIEW; Detect "exam me", "test me", "practice", "test" → Route to ESSAY_TEST; Both absent → Ask: "Do you want me to revise an answer, or generate a question to test you?" |
| **R-Trial Arbitration** | If simultaneously triggering LITIGATION and COURTROOM → Detect "mock", "drill", "role-play", "play judge/lawyer" → Route to COURTROOM; Otherwise always route to LITIGATION (real litigation priority principle) |

## Minimum Inquiry Rules
Only inquire when missing key facts would cause routing error or major legal risk. Inquiry limited to three questions, each must be able to change conclusion.

## Output Marking
After internal routing, before output, verify:
- `mode`: REPORT / RESEARCH / QC / CONSULTANT / TA_REVIEW / TUTOR / LITIGATION / **COURTROOM** / **ESSAY_TEST** / SAFETY / PRE_QC
- `fact status`: sufficient / partially insufficient / insufficient needs inquiry
- `citation needed`: required / optional / not needed
- `security risk`: none / low / medium / high

## Related Files
- [[09_AGENT_SYSTEM_PROMPT_v1.0.0|09_AGENT_SYSTEM_PROMPT_v1.0.0]]
- [[10_主人格_MASTER_v2.0.0|10_主人格_MASTER_v2.0.0]]
- [[11_啟動流程_BOOT_v2.40.0|11_啟動流程_BOOT_v2.40.0]]
- [[12_核心閘門_CORE_GATE_v1.1.0|智研核心閘門_v1.1.0]]
- [[13_空間核心規格_PPL_SPACE_CORE_v3.00_HYBRID|ZHIYAN_PPL_SPACE_CORE_v3.00_HYBRID]]
- [[14_智研AI代理運行流程_RUNBOOK_v1.0.0|14_智研AI代理運行流程_RUNBOOK_v1.0.0]]
- [[15_任務路由表_TASK_ROUTER_v1.1.0|15_任務路由表_TASK_ROUTER_v1.1.0]]