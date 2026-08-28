import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { Agent } from "../../erp-agent-odoo-deps/pi/packages/agent/src/index.ts";
import { openAICompletionsApi } from "../../erp-agent-odoo-deps/pi/packages/ai/src/api/openai-completions.lazy.ts";

const scenario = process.argv[2];
const outputPath = process.argv[3];
if (!scenario || !outputPath) throw new Error("usage: pi_model_probe.ts SCENARIO OUTPUT");

const apiKey = process.env.LLM_API_KEY;
const baseUrl = process.env.LLM_BASE_URL;
const modelId = process.env.LLM_MODEL;
if (!apiKey || !baseUrl || !modelId) throw new Error("missing LLM configuration");

const model = {
	id: modelId,
	name: modelId,
	api: "openai-completions",
	provider: "commandcode",
	baseUrl,
	reasoning: true,
	input: ["text"],
	cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
	contextWindow: 128000,
	maxTokens: 2048,
	compat: { supportsReasoningEffort: true, thinkingFormat: "openai" },
} as const;

const multiply = {
	name: "multiply",
	label: "Multiply",
	description: "Multiply two integers.",
	parameters: {
		type: "object",
		properties: { a: { type: "integer" }, b: { type: "integer" } },
		required: ["a", "b"],
		additionalProperties: false,
	},
	async execute(_id: string, args: { a: number; b: number }) {
		return { content: [{ type: "text", text: String(args.a * args.b) }], details: { ...args } };
	},
} as any;

const toolScenario = scenario === "tool";
const streamSimple = openAICompletionsApi().streamSimple;
const payloads: unknown[] = [];
const events: Array<{ atMs: number; event: unknown }> = [];
const started = performance.now();
let turns = 0;
const agent = new Agent({
	streamFn: streamSimple,
	getApiKey: () => apiKey,
	sessionId: `parity-${scenario}`,
	onPayload: (payload) => {
		payloads.push(payload);
	},
	shouldStopAfterTurn: () => ++turns >= 3,
	initialState: {
		systemPrompt: toolScenario
			? "You are a deterministic harness probe. You must call multiply exactly once for multiplication, then answer with its result."
			: "Reply exactly PONG.",
		model: model as any,
		thinkingLevel: "high",
		tools: toolScenario ? [multiply] : [],
	},
});
agent.subscribe((event) => events.push({ atMs: performance.now() - started, event }));

agent
	.prompt(toolScenario ? "Use multiply to calculate 17 * 23, then state the result." : "Reply exactly PONG.")
	.then(() => {
		const receipt = {
			identity: { entrant: "pi", scenario, model: modelId, baseUrl, reasoning: "high" },
			durationMs: performance.now() - started,
			events,
			payloads,
			coverage: { providerInputLayer: "wire-payload" },
			messages: agent.state.messages,
		};
		mkdirSync(dirname(outputPath), { recursive: true });
		writeFileSync(outputPath, JSON.stringify(receipt, null, 2), "utf8");
	})
	.catch((error) => {
		console.error(error);
		process.exitCode = 1;
	});
