# BMAD-METHOD Quick Start Guide

## 🎉 Installation Successful!

You now have BMAD-METHOD configured for:
- ✅ **Gemini CLI** - 25 BMAD commands available
- ✅ **OpenCode IDE** - 18 agents + 7 workflows
- ✅ **Claude CLI** - Available

---

## 🚀 How to Start - Choose Your Tool

### Option 1: Gemini CLI (Recommended)

**To use:**
```bash
# Just type in your terminal:
gemini

# Then in Gemini interface, type:
/bmad:agents:bmm:analyst
```

**What it does:**
- Reads `.gemini/commands/bmad-agent-bmm-analyst.toml`
- Loads the BMAD Analyst agent
- Agent guides you through workflows

**Example session:**
```
You: /bmad:agents:bmm:analyst
Gemini: [Loads Analyst agent]
Analyst: Hello! I'm the BMAD Analyst agent. How can I help you?
Analyst: Choose an option:
  1. workflow-init - Initialize your project and recommend a track
  2. generate-project-context - Analyze your codebase
  ...

You: 1
Analyst: [Analyzes your project...]
Analyst: I recommend the "BMad Method" track for your project.
Analyst: Next steps:
  1. Load PM agent: /bmad:agents:bmm:pm
  2. Create a PRD
  ...
```

---

### Option 2: OpenCode IDE

**To use:**
```bash
# Launch OpenCode:
opencode

# Then open an agent file:
# File → Open → .opencode/agent/bmad-agent-bmm-analyst.md
```

**What it does:**
- Opens the agent configuration file
- Agent loads from `_bmad/modules/bmm/agents/analyst.agent.yaml`
- Shows interactive menu

**Example session:**
```
[OpenCode loads bmad-agent-bmm-analyst.md]

┌─────────────────────────────────────┐
│  BMAD Analyst Agent               │
├─────────────────────────────────────┤
│  1. workflow-init                 │
│  2. generate-project-context         │
│  3. analyze-tech-stack             │
└─────────────────────────────────────┘

Your choice: 1
[Agent runs workflow-init...]
```

---

### Option 3: Claude CLI

**To use:**
```bash
claude
```

Claude can use BMAD agents through OpenCode-style files or custom integrations.

---

## 📋 All Available Commands

### Gemini CLI Commands (25 total)

#### BMad Method Agents (9):
```bash
/bmad:agents:bmm:analyst          # Project analysis & recommendations
/bmad:agents:bmm:pm                # Product management
/bmad:agents:bmm:architect         # System architecture
/bmad:agents:bmm:dev              # Development
/bmad:agents:bmm:sm               # Scrum Master
/bmad:agents:bmm:tech-writer       # Technical documentation
/bmad:agents:bmm:ux-designer       # UI/UX design
/bmad:agents:bmm:tea              # Meeting moderation
/bmad:agents:bmm:quick-flow-solo-dev  # Quick development
```

#### BMad Builder Agents (3):
```bash
/bmad:agents:bmb:agent-builder     # Create agents
/bmad:agents:bmb:workflow-builder    # Create workflows
/bmad:agents:bmb:module-builder    # Create modules
```

#### Creative Intelligence Agents (5):
```bash
/bmad:agents:cis:brainstorming-coach      # Brainstorming facilitation
/bmad:agents:cis:creative-problem-solver  # Creative problem solving
/bmad:agents:cis:design-thinking-coach     # Design thinking
/bmad:agents:cis:innovation-strategist   # Innovation strategy
/bmad:agents:cis:storyteller           # Storytelling
```

#### Core Agents (1):
```bash
/bmad:agents:core:bmad-master       # Master control
```

#### Workflows (7):
```bash
/bmad:workflows:core:brainstorming          # Brainstorming session
/bmad:workflows:core:party-mode             # Multi-agent collaboration
/bmad:workflows:bmm:generate-project-context # Project analysis
/bmad:workflows:bmb:agent                  # Agent creation
/bmad:workflows:bmb:create-module          # Module creation
/bmad:workflows:bmb:module                 # Module setup
/bmad:workflows:bmb:workflow               # Workflow creation
```

---

### OpenCode IDE Files (25 total)

#### Agent Files (18):
```
.opencode/agent/
├── bmad-agent-bmm-analyst.md
├── bmad-agent-bmm-architect.md
├── bmad-agent-bmm-dev.md
├── bmad-agent-bmm-pm.md
├── bmad-agent-bmm-sm.md
├── bmad-agent-bmm-tech-writer.md
├── bmad-agent-bmm-ux-designer.md
├── bmad-agent-bmm-tea.md
├── bmad-agent-bmm-quick-flow-solo-dev.md
├── bmad-agent-bmb-agent-builder.md
├── bmad-agent-bmb-workflow-builder.md
├── bmad-agent-bmb-module-builder.md
├── bmad-agent-cis-brainstorming-coach.md
├── bmad-agent-cis-creative-problem-solver.md
├── bmad-agent-cis-design-thinking-coach.md
├── bmad-agent-cis-innovation-strategist.md
├── bmad-agent-cis-storyteller.md
└── bmad-agent-core-bmad-master.md
```

#### Workflow Files (7):
```
.opencode/command/
├── bmad-bmm-generate-project-context.md
├── bmad-core-brainstorming.md
├── bmad-core-party-mode.md
├── bmad-bmb-agent.md
├── bmad-bmb-create-module.md
├── bmad-bmb-module.md
└── bmad-bmb-workflow.md
```

---

## 🎯 Recommended Starting Point

### For New Projects:

**Step 1: Analyze**
```bash
# In Gemini:
/bmad:agents:bmm:analyst

# Or in OpenCode:
# Open file: .opencode/agent/bmad-agent-bmm-analyst.md
# Choose: workflow-init
```

**Step 2: Plan**
```bash
# Analyst will recommend a track. Let's say it recommends "BMad Method"
/bmad:agents:bmm:pm

# Create your PRD (Product Requirements Document)
```

**Step 3: Design**
```bash
/bmad:agents:bmm:architect

# Create technical architecture
```

**Step 4: Build**
```bash
/bmad:agents:bmm:dev

# Implement your features
```

---

### For Bug Fixes / Quick Changes:

```bash
/bmad:agents:bmm:quick-flow-solo-dev

# This agent is optimized for rapid development
# Will guide you through tech spec + implementation
```

---

### For Brainstorming / Ideas:

```bash
/bmad:agents:cis:brainstorming-coach

# Or use:
/bmad:workflows:core:brainstorming
```

---

### For Project Analysis:

```bash
/bmad:workflows:bmm:generate-project-context

# Analyzes your codebase and creates documentation
```

---

## 💡 Pro Tips

### In Gemini CLI:
- **Use autocomplete**: Type `/bmad:` and press tab
- **Multi-agent workflows**: Try `/bmad:workflows:core:party-mode` for team collaboration
- **Context preservation**: Agents remember previous context within the session

### In OpenCode:
- **Fresh chats**: Use new chat for each workflow
- **Agent files**: All agents reference `_bmad/modules/*/agents/*.agent.yaml`
- **Workflow files**: Workflows are in `.opencode/command/`

### General:
- **Start with analyst**: Always good to begin with `/bmad:agents:bmm:analyst`
- **Follow the workflow**: Agents guide you through proven development processes
- **Ask for clarification**: If unsure, ask the agent what to do next

---

## 📚 Learn More

- **Quick Start**: [BMad Method Quick Start](https://github.com/bmad-code-org/BMAD-METHOD/blob/main/docs/modules/bmm-bmad-method/quick-start.md)
- **Full Docs**: [BMAD Documentation](https://github.com/bmad-code-org/BMAD-METHOD/blob/main/docs/index.md)
- **Community**: [Discord](https://discord.gg/gk8jAdXWmj)
- **Changelog**: [Latest Updates](https://github.com/bmad-code-org/BMAD-METHOD/blob/main/CHANGELOG.md)

---

## ✅ Ready to Go!

**What do you want to do?**

1. **"Start new project"** → Run: `/bmad:agents:bmm:analyst` (in Gemini)
2. **"Fix a bug"** → Run: `/bmad:agents:bmm:quick-flow-solo-dev`
3. **"Brainstorm"** → Run: `/bmad:agents:cis:brainstorming-coach`
4. **"Analyze code"** → Run: `/bmad:workflows:bmm:generate-project-context`
5. **"Learn more"** → Read the documentation links above

**Just type one of these or describe what you want to build!**
