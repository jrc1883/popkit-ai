// Example: Health Check Tool Implementation

export const checkService = {
  name: "[project]__check_[service]",
  description: "Check if [service] is running on port [port]",
  inputSchema: {
    type: "object",
    properties: {},
    required: []
  },
  async execute() {
    const response = await fetch(`http://localhost:[port]/health`);
    return {
      running: response.ok,
      url: `http://localhost:[port]`,
      status: response.status
    };
  }
};

// Example: Semantic Search Tool

export const toolSearch = {
  name: "[project]__tool_search",
  description: "Search for tools by description",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Natural language query" },
      top_k: { type: "number", default: 5 }
    },
    required: ["query"]
  },
  async execute({ query, top_k = 5 }) {
    const tools = getAllTools();
    return rankByRelevance(tools, query, top_k);
  }
};
