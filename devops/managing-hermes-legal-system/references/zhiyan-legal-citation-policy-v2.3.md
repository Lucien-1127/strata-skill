# Zhiyan Legal Citation Policy v2.3.0 Example

## File Location
`docs/20_模式與引用層/30_引用政策_CITATION_POLICY_v2.0.0.md`

## Overview
This file defines the citation policy for the Zhiyan AI Legal System, ensuring all legal references are verifiable and preventing hallucination of legal provisions.

## Version History
| Version | Date | Main Changes |
|---------|------|--------------|
| v1.0 | 2026-01-15 | Initial version: forced (舊式S1)(舊式S2) format, dense inline |
| v2.0 | 2026-01-16 | Optimized: changed to superscript+end table; reduced interference |
| v2.1 | 2026-06-25 | Added [T1][T2] RAG citation source references |
| v2.2 | 2026-07-04 | Added C5.4 source credibility level correspondence rules (coupled with core gate) |
| v2.3 | 2026-07-05 | Unified format: sentence-terminal superscript + end list |

## Effective Date
Starting 2026-01-17, all QC/RESEARCH/REPORT modes automatically apply v2.0 rules.
Starting 2026-07-05, all modes apply v2.3 format.

## C0. Existence Verification Rules (v1.0, Effective)
### C0.1 Taiwan Civil Code Article Number Hard Boundary
- Taiwan Civil Code has five volumes (General Provisions, Obligations, Property Rights, Family, Inheritance), article numbers range from **§1 – §1225**.
- ✅ **Legal Range**: Article numbers §1–§1225 within the Civil Code can be normally cited and discussed.
- ❌ **Illegal Range**: Article numbers §1226 and above **do not exist in Taiwan Civil Code**.
- If users cite article numbers above §1225, must respond: "Taiwan Civil Code has no this article number, please confirm if you misremembered the article number?"
- Strictly prohibited to fabricate content for non-existent article numbers.

### C0.2 Repealed/Deleted Articles List (as of 2024)
The following articles have been repealed due to legislative amendments and are no longer valid. If cited, must be marked as "repealed" and explain the repeal background:

| Article Number | Original Chapter/Section | Repeal Time | Repeal Reason |
|:---|:---|:---|:---|
| §987 | Family Law / Engagement | 2007 Civil Code Amendment | Engagement age restriction provisions repealed |
| §991 | Family Law / Marriage | 2007 Civil Code Amendment | Minor marriage consent rights related provisions repealed |
| §992 | Family Law / Marriage | 2007 Civil Code Amendment | Marriage annulment related provisions repealed |

### C0.3 Judgment Number Authenticity Disclaimer
This system **cannot verify the authenticity of judgment numbers**. When citing the following, must add disclaimer:
- Supreme Court judgments (e.g., "Taiwan Shang Zi Di XXXX Hao")
- High Court judgments
- Administrative Court judgments
- Constitutional Court interpretations / Constitutional Court judgments
- Various levels of civil/criminal court meeting resolutions

**Format Specification**: Whenever citing specific judgment numbers, must add in the response:
> ⚠️ **Judgment Authenticity Disclaimer**: The above judgment numbers are system-generated and may not correspond to actual judgments. Please verify yourself at the Judicial Judgment Query System (https://judgment.judicial.gov.tw).

### C0.4 Citation Timeliness Check
Before citing any provision, first confirm:
1. Whether the article number is within §1–§1225 range
2. Whether the article number is in the repealed list
3. If involving Civil Code Family Law articles (§967–§1137), pay special attention to articles repealed in the 2007 amendment

## C1. Citation Strategy (v2.1)
### C1.1 Source Citation Reference Correspondence
| Prefix | Source | Priority | Description |
|:----:|:---|:---:|:---|
| `[T1]` | Local Vernacular RAG | **Highest** | 47K entries of legal provisions vernacular abstracts, cite with original article number and abstract |
| `` | National Legal Database | Secondary | law.moj.gov.tw |
| `` | Judicial Judgment Query | Secondary | judgment.judicial.gov.tw |
| `` | Academic Papers / Textbooks | General | |

### C1.2 In-text Citation Principles
- **RAG Priority**: First check local RAG, if vernacular abstract exists then directly cite [T1], if abstract insufficient then supplement with network [1]
- **First Mention of New Source**: Add [T1], [1], [2], [3]… at the end of that sentence
- **Repeated Same Source Citation**: No need to re-mark; first marking already established correspondence
- **Direct Quotation**: Add citation source reference after the quotation
- **Goal**: Minimize inline markers, maintain text fluency

**Example (Improved Before/After):**
- ❌ Old Version (Dense Interference):  
  > Water's boiling point at room temperature is 100℃（旧式S1）, this is common knowledge（旧式S2）. Water flows downwards（旧式S3）, forming waterfalls（旧式S4）.
- ✅ New Version (Clean and Readable):  
  > Water's boiling point at room temperature is 100℃[1]. Water flows downwards, forming waterfalls[2].

### C1.2 Citation Timing (When to Add, When Not to Add)
| Situation | Handling | Reason |
|:---|:---:|:---|
| Clear data/statistics | Add [1] | Must be traceable |
| Statements of fact (general knowledge) | Add [1] (first time) | Trace source origin |
| Restating opponent's claim | Add [数字] | Mark the speaker's role |
| Own reasoning | Do not add | Logical derivation, not citation |
| Repeating same fact | Do not add | Already marked in first mention |

## C2. Citation Marking Format (Unified Standard)
### C2.1 Paragraph-end Reference Table
At the end of each response paragraph, use the following format to list the paragraph's cited sources:

```
【本段資料來源】
^[來源簡稱1]
^[來源簡稱2]
^[來源簡稱3]
```

### C2.2 Complete Paragraph Citation Representation Example
**Paragraph Content:**
> Artificial intelligence is changing industrial structure. According to the 2024 survey[1], 89% of enterprises have already introduced AI tools[2]. Experts predict that in the next five years, 40% of job roles will be transformed[3].

**Paragraph End Marking:**
```
【本段資料來源】
^[1]
^[2]
^[3]
```

## C3. Full-text Source List (Summary Table) (Optional, Recommended for REPORT Mode)
### C3.1 When to Use
- When the response contains **3 or more paragraphs**, each with different sources
- End uses "unified source list" to aggregate, avoid duplicate listings

### C3.2 Format Template
```
【完整資料來源清單】
[1] Title — Media / Institution
    Website: URL
    Update Time: 2026-01-16
    Credibility Level: [Official / Academic / Industry / Media]

[2] Title — Media / Institution
    Website: URL
    Remarks: If from uploaded file, record file name and page number

[3] Title — Media / Institution
    ...
```

### C3.3 Credibility Level Annotation (Optional, Recommended for REPORT Mode)
- **[Official]**: Official data, government documents, corporate financial reports
- **[Academic]**: Academic journal papers, research institution reports
- **[Industry]**: Industry reports, professional associations
- **[Media]**: News media, commentary articles
- **[User-Provided]**: User-uploaded files

## C4. Three MODE Adaptation Rules
### C4.1 MODE_QC (Quality Check)
```plaintext
【Output Structure】
1) Core Conclusion
2) Basis (by item)
3) Conflict Check
4) Risk and Boundary
5) Data Source

【Citation Method】
- Each "basis" item after add ¹²³…
- End unified list "【Data Source】" table
- If conflict check has conflicting sources, mark as [X vs Y]
```

### C4.2 MODE_RESEARCH (Research Report)
```plaintext
【Output Structure】
1) Core Conclusion
2) Basis (official→academic→media layered)
3) Conflict Check
4) Risk and Boundary
5) Data Source

【Citation Method】
- Key discussion parts add [數字]
- Layered basis list: each layer separately marked [1][2][3]…
- End unified list "【完整資料來源清單】" with credibility level
```

### C4.3 MODE_REPORT (Formal Report)
```plaintext
【Output Structure】
1) Core Conclusion
2) Basis (3-6 key dependencies, each at least 1 source)
3) Conflict Check
4) Risk and Boundary
5) Data Source

【Citation Method】
- Each "basis" paragraph end tag [1][2]…
- End unified list "【完整資料來源清單】"
- Includes credibility level [Official][Academic] etc.
- If report exceeds 3000 words, can be chaptered and listed
```

## C5. Special Situation Handling
### C5.1 Citation of Uploaded Files
Format:
```
【本段資料來源】
[1] Filename — Upload:文件UUID / 簡稱
    Page / Chapter: 第 X 頁或「第 X 節」
    Quotation: "..." [粗摘錄位置]
```

### C5.2 Citation of Google Drive Linked Files
```
【本段資料來源】
[1] 01_SPACE_INSTRUCTIONS.txt — Space Files
    Source Link: Google Drive / 智研 Space
    Sync Time: 2026-01-16
```

### C5.3 Multiple Versions of Same Source (Avoid Citation Confusion)
```
【本段資料來源】
[1] McKinsey Report 2024 (v1.0) — https://example.com/mckinsey-2024-v1
[2] McKinsey Report 2024 (v2.0 updated) — https://example.com/mckinsey-2024-v2
```

## C6. Inspection Standard
### C6.1 What is "Conflict"?
- Same fact, different data from different sources → **Data Conflict**
- Same definition, different terminology from different sources → **Definition Conflict**
- Different time points leading to opposite conclusions → **Time Conflict**

### C6.2 Conflict Marking Method
```
【Conflict Check】
Scope: 2024 AI Adoption Rate Statistics

Divergence Points:
- Source A[1] reports 89% of enterprises adopt AI
- Source B[2] reports 65% of enterprises adopt AI
- Cause of difference: definition scope differs (former includes "small-scale experiments"; latter limits to "formal production environment")
- Conclusion: This response adopts 【Scope-definite Source B】 as main basis
```

## C7. Quality Inspection Checklist (Internal Use)
Before each output, self-check:
| Item | Check Point | Pass |
|------|-------------|------|
| inline 標記 | First citation adds [數字], repeated no addition | ✓ |
| 段落末尾 | If there is citation, must list "【本段資料來源】" | ✓ |
| 全文末尾 | If paragraph count ≥3, end adds "【完整資料來源清單】" | ✓ |
| 數字連貫 | [1][2][3]… no jumps, no repeats | ✓ |
| 信度標註 | REPORT mode must mark [Official] etc. | ✓ |
| 衝突揭示 | If conflicting data, must explain in "衝突檢查" section | ✓ |
| 超連結可用 | All URLs clickable (no typos, complete) | ✓ |

## C8. Common Questions and Examples
### Q: Can I omit sources?
A: **No**. Even "common knowledge" must be marked on first mention. For example:
- ❌ Boiling point of water is 100℃（未標）
- ✅ Boiling point of water is 100℃[1]

### Q: If multiple sources in one paragraph, how to mark?
A: By appearance order:
> China's GDP 2024年成長 5.2%[1]，超越預期[2]，專家預測[3]...
```
【本段資料來源】
[1] China National Bureau of Statistics Official Announcement — URL
[2] IMF World Economic Outlook Report — URL
[3] Economist Commentary Article — URL
```

### Q: If the whole text only has 2 citations, do I need "complete list"?
A: **No need**. Only add "【本段資料來源】" at paragraph end. Full list used for "multi-paragraph, multi-source" situations.

### Q: Can I insert hyperlinks in text instead of numeric markers?
A: **Possible, but not recommended**. Reasons:
- ❌ Hyperlinks easy to mis-click, reduce reading fluency
- ✓ Numeric markers + end list: cleaner, easier to scan

## Version Management
| Version | Date | Main Changes |
|:---:|:---:|:---|
| v1.0 | 2026-01-15 | Initial version: forced （舊式S1）（舊式S2） format, dense inline |
| v2.0 | 2026-01-16 | Optimization: changed to 上標+end table; reduced interference |
| v2.1 | 2026-06-25 | Added [T1][T2] RAG citation source references |
| v2.2 | 2026-07-04 | Added C5.4 來源可信度分級對應規則 (coupled with core gate) |
| v2.3 | 2026-07-05 | Unified format: sentence-terminal superscript + end list |

## Effective Date
**Starting 2026-01-17, all QC/RESEARCH/REPORT modes automatically apply v2.0 rules**
**Starting 2026-07-05, all modes apply v2.3 format**

## Related Documents
- [[20_模式_REPORT_報告_v2.0.0|正式報告模板 v2.0（MODE_REPORT）]]
- [[21_模式_RESEARCH_研究_v2.0.0|研究報告模板 v2.0（MODE_RESEARCH）]]
- [[22_模式_QC_查核_v2.0.1|品質檢查模板 v2.0.1（MODE_QC｜審計降噪版）]]
- [[31_引用升級手冊_v2.0.0|ZHIYAN Citation Policy v2.0 優化完成手冊]]
- [[32_引用政策優化完成手冊_v2.0.0|33_引用政策優化完成手冊_v2.0.0]]