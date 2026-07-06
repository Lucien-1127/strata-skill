# FEG_CORE_EXTREME DSL 權威參考（共享）

> FEG (Finite Execution Graph) 極限壓縮技術 — 源自 RTCKD_KERNEL v6.4.3_EXTREME_FEG_MIRROR
> 核心公理：`C = compress_internal_not_external`
> 
> **此文件為 STRATA 生態系統中所有 FEG 實作的統一權威參考**。引用者：prompt-factory-7-1、hermes-skill-author、decision-graph-router。

## DSL 結構

```
FEG_CORE_EXTREME[
D{...};   // 維度定義
S1..5;    // 量表
P:...;    // Pass 條件
R:...;    // Revise 條件
Dg:...;   // Downgrade 條件
C:...;    // Confirm 觸發
B:...;    // Block 觸發
V:...;    // 條件分支
M:...;    // 決策→行動映射
]
```

## 區塊語法

| 區塊 | 語法 | 範例 |
|------|------|------|
| `D{...}` | 逗號分隔維度名稱 | `D{Struct,Clarity,Exec}` |
| `S..` | 量表範圍 | `S1..5`（1~5 分）|
| `P:` | AND(&) 連結條件 | `P:A4&B4&C4`（A>=4 AND B>=4 AND C>=4）|
| `R:` | OR(\|) 連結條件 | `R:A<4\|B<4`（A<4 OR B<4）|
| `Dg:` | AND(&) 連結條件 | `Dg:E<3&G<3` |
| `C:` | OR(\|) 連結條件 | `C:AMB\|RM\|FU` |
| `B:` | OR(\|) 連結條件 | `B:F<3\|SB\|BH\|QF` |
| `V:` | ternary `?(true):(false)` | `V:VM?(SCH=VMS&VAR3&NEG1):OK` |
| `M:` | 分號分隔映射 `>` | `M:P>DLV;R>RTY` |

## FEG 層級

| 層級 | 壓縮比 | 說明 |
|------|--------|------|
| FEG-L1 | ~50% | 精簡自然語言，去冗詞 |
| FEG-L2 | ~30% | DSL 符號化 — 不同對象有不同的 FEG-L2 格式 |
| FEG-L3 | ~15% | FEG_CORE_EXTREME（含決策矩陣）— 統一格式 |

## FEG-L2：三種 DSL 格式（依壓縮對象）

### 格式 A：通用提示詞（prompt-factory-7-1）

```
ROLE[{domain}:{角色}]
TASK[{任務濃縮}]
IN[{輸入格式}]
OUT[{輸出結構}]
CON[{約束}]
```

### 格式 B：SKILL.md 技能檔（hermes-skill-author）

```
FEG_SKILL[
N:{name}
D:{description ≤60}
V:{version}
T:{tags}
WHEN:{觸發詞濃縮}
RUN:{How-to-Run 濃縮}
PROC:{步驟濃縮}
PIT:{陷阱濃縮}
]
```

### 格式 C：決策圖路由（decision-graph-router）

```
FEG{
  D{A|B|C|G}              # 域宣告
  V:VM?                    # 多域模式 flag
}
RULES{
  SAFETY: {禁止事項}
  PRIORITY: {優先級鏈}
  FALLBACK: {降級策略}
}
|->{X}                     # 強制讀取狀態快照
STATES{
  NORMAL: DONE
  PARTIAL: {部分完成說明}
  CLARIFY: {回問條件}
  ABORT: {中斷條件}
}
```

## FEG-L3 實例：SKILL.md → FEG_CORE_EXTREME 映射

將 hermes-skill-author 的 HARDLINE_RULES 評分規則映射為 FEG_L3：

```
FEG_CORE_EXTREME[
D{FRONT,DESC,NAME,TOOLS,SECT,BAN,AUTH,REUSE};
S1..5;
P:FRONT>=5&DESC>=5&NAME>=5&TOOLS>=5&SECT>=5&BAN>=5&AUTH>=5&REUSE>=5;
R:FRONT<5|DESC<5|NAME<5|TOOLS<5|SECT<5|BAN<5|AUTH<5|REUSE<5;
Dg:BAN<4&REUSE<4;
C:TOOLS<3|SECT<3;
B:BAN<3|REUSE<3|SF|BH|QF;
V:VM?(SCH=SKILL&FEG-L3&NEG1):OK;
M:P>DLV;R>RTY(max=2);Dg>SAFE;C>ASK;B>STOP
]
```

維度映射：FRONT=Frontmatter / DESC=description / NAME=name格式 / TOOLS=Hermes-tool framing / SECT=段落完整 / BAN=禁止詞 / AUTH=author正確 / REUSE=可重用性

## 標準維度映射（PROMPT_EVALUATOR_V3 → FEG_CORE）

```
A = 結構完整性 (Struct)
B = 清晰度 (Clarity)
C = 可執行性 (Exec)
D = 約束有效性 (Constr)
E = Token 效率 (Token)
F = 領域對齊 (Domain)
G = 語義品質 (Semantic)
```

## 動作映射（M:）

| 代碼 | 含義 |
|------|------|
| DLV | Deliver — 直接交付 |
| RTY | Retry — 重試/修復（可帶 max=N 限制次數） |
| SAFE | Safe — 降級安全輸出 |
| ASK | Ask — 請求人工確認 |
| STOP | Stop — 停止/阻擋 |

## 跨技能引用表

| 技能 | 使用的 FEG 格式 | FEG-L2 格式 | 有 FEG-L3 實例 |
|:-----|:-------------|:-----------|:-------------:|
| prompt-factory-7-1 | 格式 A（通用提示詞） | ROLE/TASK/IN/OUT/CON | ✅ PROMPT_EVALUATOR_V3 映射 |
| hermes-skill-author | 格式 B（SKILL.md） | N/D/V/T/WHEN/RUN/PROC/PIT | ✅ HARDLINE_RULES 映射（見本文） |
| decision-graph-router | 格式 C（決策圖路由） | FEG{}/RULES{}/STATES{} | 🟡 使用精簡版 FEG-C 語法，非完整 DSL |
