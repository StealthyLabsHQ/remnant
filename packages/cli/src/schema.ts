import { z } from "zod";

export const AgentSchema = z.enum(["claude-code", "codex", "other"]);

export const RemnantSchema = z.object({
  projectName: z.string().min(1),
  session: z.object({
    date: z.string().datetime(),
    agent: AgentSchema,
    duration: z.number().int().min(0),
  }),
  done: z.array(z.string()),
  failed: z.array(z.string()),
  state: z.array(z.string()),
  next: z.array(z.string()),
  blockers: z.array(z.string()),
});

export type Remnant = z.infer<typeof RemnantSchema>;
export type Agent = z.infer<typeof AgentSchema>;

const sectionNames = ["Done", "Failed", "State", "Next", "Blockers"] as const;
type SectionName = (typeof sectionNames)[number];

export function createEmptyRemnant(projectName: string, agent: Agent = "codex"): Remnant {
  return {
    projectName,
    session: {
      date: new Date().toISOString(),
      agent,
      duration: 0,
    },
    done: [],
    failed: [],
    state: [],
    next: [],
    blockers: [],
  };
}

export function parseRemnantMarkdown(markdown: string): Remnant {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const title = lines.find((line) => line.startsWith("# Remnant "));
  const titleMatch = title?.match(/^# Remnant\s+(?:\u2014|-)\s+(.+)$/u);

  if (!titleMatch) {
    throw new Error("Invalid REMNANT.md: missing '# Remnant - <project-name>' title");
  }

  const session = parseSession(lines);
  const sections = Object.fromEntries(sectionNames.map((name) => [name, parseListSection(lines, name)])) as Record<
    SectionName,
    string[]
  >;

  return RemnantSchema.parse({
    projectName: titleMatch[1].trim(),
    session,
    done: sections.Done,
    failed: sections.Failed,
    state: sections.State,
    next: sections.Next,
    blockers: sections.Blockers,
  });
}

export function renderRemnantMarkdown(remnant: Remnant): string {
  const data = RemnantSchema.parse(remnant);

  return [
    `# Remnant \u2014 ${data.projectName}`,
    "",
    "## Session",
    `- date: ${data.session.date}`,
    `- agent: ${data.session.agent}`,
    `- duration: ${data.session.duration}`,
    "",
    "## Done",
    renderList(data.done),
    "",
    "## Failed",
    renderList(data.failed),
    "",
    "## State",
    renderList(data.state),
    "",
    "## Next",
    renderList(data.next),
    "",
    "## Blockers",
    renderList(data.blockers),
    "",
  ].join("\n");
}

function parseSession(lines: string[]): Remnant["session"] {
  const start = lines.findIndex((line) => line.trim() === "## Session");
  if (start === -1) {
    throw new Error("Invalid REMNANT.md: missing Session section");
  }

  const values: Record<string, string> = {};
  for (const line of lines.slice(start + 1)) {
    if (line.startsWith("## ")) {
      break;
    }

    const match = line.match(/^- ([^:]+):\s*(.*)$/u);
    if (match) {
      values[match[1].trim()] = match[2].trim();
    }
  }

  return {
    date: values.date ?? "",
    agent: AgentSchema.parse(values.agent),
    duration: Number.parseInt(values.duration ?? "", 10),
  };
}

function parseListSection(lines: string[], name: SectionName): string[] {
  const start = lines.findIndex((line) => line.trim() === `## ${name}`);
  if (start === -1) {
    throw new Error(`Invalid REMNANT.md: missing ${name} section`);
  }

  const items: string[] = [];
  for (const line of lines.slice(start + 1)) {
    if (line.startsWith("## ")) {
      break;
    }

    const match = line.match(/^- ?(.*)$/u);
    if (match && match[1].trim()) {
      items.push(match[1].trim());
    }
  }

  return items;
}

function renderList(items: string[]): string {
  if (items.length === 0) {
    return "-";
  }

  return items.map((item) => `- ${item}`).join("\n");
}
