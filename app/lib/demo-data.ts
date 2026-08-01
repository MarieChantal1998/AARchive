export type Scene = {
  id: string;
  start: number;
  end: number;
  range: string;
  summary: string;
  excerpt: string;
  tags: string[];
  confidence: number;
  issue?: string;
  positive?: string;
  activities: string[];
  roles: string[];
  equipment: string[];
  environment: string[];
};

export const DEMO_VIDEO_URL =
  "https://d34w7g4gy10iej.cloudfront.net/video/2606/DOD_111741836/DOD_111741836-1920x1080-9000k.mp4";

export const DEMO_THUMBNAIL =
  "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/USAG-Italy_DES_Integrated_Emergency_Exercise_%281008879%29.webm/960px--USAG-Italy_DES_Integrated_Emergency_Exercise_%281008879%29.webm.jpg";

export const projects = [
  {
    id: "demo-coordinated-response",
    title: "Integrated Emergency Response Exercise",
    type: "Emergency response / triage",
    date: "Apr 29, 2026",
    duration: "00:57",
    status: "Ready",
    scenes: 5,
    briefs: 1,
    thumbnail: DEMO_THUMBNAIL,
    storage: "Public demo · B2-ready",
    description:
      "Public-domain exercise footage showing an integrated natural-disaster and mass-casualty response scenario.",
  },
  {
    id: "warehouse-evacuation",
    title: "Warehouse Evacuation Tabletop",
    type: "Evacuation procedure",
    date: "Jul 24, 2026",
    duration: "18:42",
    status: "Ready",
    scenes: 12,
    briefs: 2,
    thumbnail: "",
    storage: "B2 metadata example",
    description: "Synthetic library record included to demonstrate mixed exercise collections.",
  },
  {
    id: "field-comms-drill",
    title: "Field Communications Drill",
    type: "Team coordination",
    date: "Jul 18, 2026",
    duration: "27:16",
    status: "Indexing",
    scenes: 0,
    briefs: 0,
    thumbnail: "",
    storage: "B2 metadata example",
    description: "Synthetic processing-state example; no results are presented as complete.",
  },
];

export const scenes: Scene[] = [
  {
    id: "scene-001",
    start: 0,
    end: 9.5,
    range: "00:00–00:09",
    summary: "Responders arrive at the simulated incident area and begin staging.",
    excerpt: "Responders move into the exercise area as the simulated incident begins.",
    tags: ["arrival", "staging", "coordination"],
    confidence: 82,
    positive: "Teams establish an organized arrival pattern before moving deeper into the scene.",
    activities: ["Arrival", "Staging", "Initial coordination"],
    roles: ["First responders", "Exercise controllers"],
    equipment: ["Emergency vehicles", "Protective equipment"],
    environment: ["Outdoor training area"],
  },
  {
    id: "scene-002",
    start: 9.5,
    end: 20,
    range: "00:09–00:20",
    summary: "Teams establish a working area and coordinate the first casualty assessment.",
    excerpt: "The response team begins a structured initial assessment in the designated work area.",
    tags: ["assessment", "communication", "handoff", "roles"],
    confidence: 76,
    issue: "Some handoff details are not visually or audibly clear and require human review.",
    activities: ["Assessment", "Team communication"],
    roles: ["Medical responders", "Safety personnel"],
    equipment: ["Medical kits"],
    environment: ["Simulated disaster site"],
  },
  {
    id: "scene-003",
    start: 20,
    end: 32.5,
    range: "00:20–00:32",
    summary: "Medical personnel perform triage and prepare a simulated casualty for movement.",
    excerpt: "Medical teams continue triage while coordinating movement priorities.",
    tags: ["triage", "medical", "stretcher", "team coordination"],
    confidence: 87,
    positive: "Responders work in parallel while maintaining attention on the casualty movement path.",
    activities: ["Triage", "Casualty assessment", "Preparation for transport"],
    roles: ["Medical team", "Simulated casualty"],
    equipment: ["Stretcher", "Medical equipment"],
    environment: ["Triage area"],
  },
  {
    id: "scene-004",
    start: 32.5,
    end: 45,
    range: "00:32–00:45",
    summary: "A casualty movement is coordinated between field responders and the transport team.",
    excerpt: "The team transitions from treatment to transport and confirms the movement route.",
    tags: ["evacuation", "handoff", "equipment problem", "recovery", "transport"],
    confidence: 80,
    issue: "The transition point appears congested briefly before the route clears.",
    positive: "The team pauses, repositions, and resumes movement without abandoning the handoff.",
    activities: ["Casualty movement", "Transport handoff", "Route clearance"],
    roles: ["Transport team", "Medical responders"],
    equipment: ["Stretcher", "Ambulance"],
    environment: ["Vehicle access lane"],
  },
  {
    id: "scene-005",
    start: 45,
    end: 57,
    range: "00:45–00:57",
    summary: "Responders complete transport while maintaining coordination around the vehicle area.",
    excerpt: "Field and transport personnel close the movement sequence and continue coordinating at the vehicle.",
    tags: ["effective team coordination", "transport", "communication", "closeout"],
    confidence: 84,
    positive: "Roles remain coordinated through the final transfer instead of ending at initial contact.",
    activities: ["Transport completion", "Cross-team coordination"],
    roles: ["Field responders", "Transport personnel"],
    equipment: ["Ambulance"],
    environment: ["Transport area"],
  },
];

export const suggestedQueries = [
  "Communication during evacuation",
  "Equipment problem followed by a recovery",
  "Examples of effective team coordination",
];

export function searchScenes(query: string) {
  const terms = query.toLowerCase().match(/[a-z0-9]+/g) || [];
  return scenes
    .map((scene) => {
      const text = [scene.summary, scene.excerpt, ...scene.tags, ...scene.activities, scene.issue, scene.positive]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      const matched = terms.filter((term) => text.includes(term));
      const phraseBonus = query.length > 5 && text.includes(query.toLowerCase()) ? 2 : 0;
      const score = matched.length + phraseBonus;
      return { scene, matched: [...new Set(matched)], score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || b.scene.confidence - a.scene.confidence);
}

