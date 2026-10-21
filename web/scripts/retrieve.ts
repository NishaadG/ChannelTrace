// Runs the site's built-in retrieval assistant from the command line (used by scripts/eval_assistant.py).
// stdin: {"facts": "...", "questions": ["..."]}  stdout: ["answer", ...]
import { retrieve } from "../src/lib/assistant";

let raw = "";
process.stdin.on("data", (d) => (raw += d));
process.stdin.on("end", () => {
  const { facts, questions } = JSON.parse(raw) as { facts: string; questions: string[] };
  process.stdout.write(JSON.stringify(questions.map((q) => retrieve(facts, q))));
});
