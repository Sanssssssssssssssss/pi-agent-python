# Pi 0.84.1 parity ledger

Authority: `E:\GPTProject2\erp-agent-odoo-deps\pi` at
`534bcbffb7e1e7551d9ee3572dfeb278e203e493`.

This ledger tracks observable behavior, not similarly named classes. A row is
complete only after the matching Pi scenario has a deterministic Python test.

| Pi layer | Authoritative source | Tau target | Status |
|---|---|---|---|
| Provider messages, thinking, usage | `packages/ai/src` | `tau_ai` | Core transform/replay path covered for Anthropic, Google, Mistral, OpenAI-compatible and Codex Responses; provider-specific streaming matrices remain |
| Model/tool loop | `packages/agent/src/agent-loop.ts` | `tau_agent/loop.py` | Main ordering, hooks, parallel/sequential tools, termination, truncation and active provider/tool cancellation covered |
| Stateful Agent | `packages/agent/src/agent.ts` | `tau_agent/harness.py` | Main state/lifecycle path, per-run system replacement and settled-tool late-update guard covered |
| AgentSession | `packages/coding-agent/src/core/agent-session.ts` | `tau_coding/session.py` | Core prompt/continue, queues, transient retry, retry settlement, recoverable-length compact/retry, per-tool-turn state refresh and full tool-loop wait covered; final independent comparison pending |
| Session tree/JSONL | `packages/coding-agent/src/core/session-manager.ts` | `tau_agent/session`, `tau_coding/session_manager.py` | Active leaf, branch summary, latest-compaction context and legacy linear replay covered; fork/label/migration matrix remains |
| Compaction and branch summary | `packages/coding-agent/src/core/compaction` | `tau_coding/session.py`, `tau_coding/branch_summary.py` | Pi cut point, first-kept boundary, split-turn prefix, serialization and compact/tree extension interception covered; full fork/tree operation matrix remains |
| System prompt | `packages/coding-agent/src/core/system-prompt.ts` | `tau_coding/system_prompt.py` | Core prompt behavior aligned; Tau name/docs paths and extension section seam intentionally remain |
| Resources and skills | `resource-loader.ts`, `skills.ts`, `prompt-templates.ts` | `tau_coding/resources.py`, `skills.py`, `prompt_templates.py` | Pi YAML 1.2 frontmatter, recursive discovery, ignore files, validation, collision order, skill-before-template expansion, invocation reload and extension resource merge covered |
| Extensions | `packages/coding-agent/src/core/extensions` | `tau_coding/extensions` | Core resource/context/prompt, provider, session switch/fork/tree/compact, message replacement and tool lifecycle hooks ported; UI/command/flag surfaces remain outside this base |
| Print/JSON/RPC/interactive modes | `packages/coding-agent/src/modes` | `tau_coding` CLI/rendering/RPC/TUI | Existing implementation; unverified as a complete layer |
| Telemetry/protocol/client/server | corresponding Pi packages plus `coding-agent/src/server` | no single Tau target | Pending; no new telemetry stack will be invented |

## Current verified deltas

- Steering and follow-up have separate Pi-compatible drain modes.
- `continue_()` rejects an empty transcript and an assistant tail unless a
  queued steering or follow-up message can start the next run.
- One-at-a-time steering from an assistant tail produces one assistant response
  before the next queued steering message is injected.
- Overflow and Hugging Face route retries remove the retriable assistant failure
  from active model context while retaining persisted evidence, matching Pi's
  AgentSession retry boundary.
- The default system prompt no longer adds Tau-only date or policy bullets, and
  empty custom prompts follow Pi's default-prompt behavior.
- Subscribers receive the active cancellation signal and remain part of run
  settlement through the final `agent_end` event.
- Cancellation interrupts blocked provider iteration and tool execution instead
  of waiting for their I/O to return.
- Tool updates emitted after that tool has settled are ignored even while a
  parallel peer is still running.
- Coding-only messages remain typed in session history and are converted with
  Pi's exact branch-summary, compaction-summary, bash and custom-message rules
  only at the provider boundary.
- OpenAI-compatible replay now preserves `reasoning_text`, encrypted tool-call
  `reasoning_details`, and DeepSeek's required empty `reasoning_content` field.
- OpenAI Responses replay uses Pi's source-aware `call_id|item_id`
  normalization and exact UTF-16/`Math.imul` `shortHash`, keeping foreign tool
  calls paired with their results without oversized item IDs.
- Compaction keeps Pi's recent-turn boundary, uses `firstKeptEntryId`, supports
  split-turn prefix summaries, and serializes summaries as Pi does.
- Provider and transport errors use Pi's exact retry classifier, quota/billing
  errors remain terminal, retry backoff is abortable, and a retry waits for the
  complete tool loop before `prompt()` settles.
- A recoverable `length` stop uses Pi's output-token predicate, removes the
  failed tail, compacts once, and retries once.
- Skill loading follows Pi's recursive `SKILL.md` discovery, root precedence,
  ignore-file rules, YAML 1.2 metadata validation, first-wins collision rule,
  and invocation-time file reload.
- Extension hooks preserve tool call identity, error state, usage overrides and
  termination; provider hooks run at the real payload/header/response boundary.
- Chained `message_end` replacements require the same role and update the core
  message object before persistence, wildcard observers and later model context.
- Each follow-on tool turn refreshes the active provider, model, system prompt
  and tools from `CodingSession`, including the current prompt's system override.

## Integration status

- Real Pi/Tau plain and synthetic tool-call probes passed on the same model profile.
- The thin official-SDK MCP adapter completed a real Odoo ERP-Bench task with
  reward 100. The matching Pi baseline also scored 100; this one-task result is
  chain evidence, not a benchmark ranking.
- Compiler/child-run integration and new telemetry infrastructure remain outside
  this parity base.
- Pi's newer lane-based server `AgentHarness` remains outside scope; the coding
  CLI still uses the classic `Agent`/`AgentSession` path above as its authority.
