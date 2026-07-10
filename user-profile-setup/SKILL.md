---
name: user-profile-setup
description: Help the agent learn and store user preferences for personalized assistance.
version: 0.1.0
author: Hermes
platforms:
- linux
metadata.hermes.tags:
- Setup
- Personalization
- Memory
status: stable
---

# User Profile Setup
This skill guides the agent to collect user preferences (name, interests, environment, core rules) and persist them in Hermes user memory for future sessions. It does not modify system configs or external accounts.

## When to Use
- When starting a new conversation with a user and you need to understand their background.
- When the user mentions a preference that should be remembered across sessions.
- When you want to ensure the agent follows user-specific constraints (e.g., no fabrication).

## Prerequisites
- Hermes Agent installed and running.
- Access to the `clarify` and `memory` tools.

## How to Run
Invoke the skill via `skill_view(name='user-profile-setup')` to load its guidance, then follow the Procedure steps using the appropriate tools.

## Quick Reference
- `clarify`: ask user for information.
- `memory`: add entries to user memory.

## Procedure
1. Greet the user and explain you will build a short profile to personalize assistance.
2. Ask for preferred name using `clarify` with an open-ended question (e.g., "How should I address you?").
3. Ask for interests/domains the user wants to focus on (e.g., "What topics or fields do you enjoy working on?").
4. Ask about environment (e.g., "Where are you currently running Hermes? (e.g., local machine, Google Cloud VM)").
5. Confirm core constraints (e.g., "Do you have any specific rules I must always follow, such as never fabricating information?").
6. Save each piece of information to user memory using the `memory` tool with `action='add'` and `target='user'`.
   - For each item, call:
     ```
     memory(target='user', action='add', content='<the information>')
     ```
7. Confirm completion by informing the user the profile has been saved and summarizing what was stored.

## Pitfalls
- Forgetting to apply `target='user'` when saving to memory will store in the agent's generic memory instead.
- Overwriting existing memory entries unintentionally; using `add` is safe as it creates new entries.
- Not respecting the user's wish to skip profiling; always allow them to decline.

## Ongoing Preference Corrections

After initial setup, users may express style/format/workflow preferences mid-conversation (e.g., "remember: at the bottom of every response, note the model type"). These are **first-class skill signals**, not just memory events.

### How to handle mid-conversation preferences

1. **Save to memory** as usual (target='user', action='add') for quick recall.
2. **Identify the governing skill**: Which class of task does this preference relate to? (Response formatting → meta-prompt-review or similar; code style → a code-review skill; workflow → the relevant task skill.)
3. **Update that skill's SKILL.md**: Embed the preference as a pitfall, a formatting rule, or a step in the procedure. The preference belongs in the skill that governs *how* the task is done, not just in memory that records *who* the user is.
4. **Rationale**: Skills persist across agent updates and repo resets; memory can be cleared. A preference written into a skill is durable.

### Example: model-type footer
User says "每次回應最下方 註明模型的型號" → save to memory + update the relevant response-formatting skill to include "每則回應末尾附上當前模型型號" as a mandatory formatting rule.

## Verification
After running the steps, invoke `memory` with no parameters to view the current list and verify the new entries appear under the 'user' target.