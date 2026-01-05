const path = require('node:path');
const fs = require('fs');

// Constants
const bmadDir = path.join(__dirname, '_bmad');
const projectDir = __dirname;
const modules = ['bmm', 'bmb', 'cis', 'core'];

// Helper function to collect agent files
function collectAgents() {
  const agents = [];
  for (const module of modules) {
    const agentsDir = path.join(bmadDir, 'modules', module, 'agents');
    if (fs.existsSync(agentsDir)) {
      const files = fs.readdirSync(agentsDir);
      for (const file of files) {
        if (file.endsWith('.agent.yaml')) {
          const name = file.replace('.agent.yaml', '');
          agents.push({ module, name, agentPath: path.join(agentsDir, file) });
        }
      }
    }
  }
  return agents;
}

// Helper function to collect workflow files
function collectWorkflows() {
  const workflows = [];
  for (const module of modules) {
    const workflowsBaseDir = path.join(bmadDir, 'modules', module, 'workflows');
    if (fs.existsSync(workflowsBaseDir)) {
      const workflowDirs = fs.readdirSync(workflowsBaseDir, { withFileTypes: true });
      for (const dir of workflowDirs.filter(d => d.isDirectory())) {
        const workflowFile = path.join(workflowsBaseDir, dir.name, 'workflow.md');
        if (fs.existsSync(workflowFile)) {
          workflows.push({ module, name: dir.name, path: workflowFile });
        }
      }
    }
  }
  return workflows;
}

// Helper function to collect task files
function collectTasks() {
  const tasks = [];
  for (const module of modules) {
    const tasksDir = path.join(bmadDir, 'modules', module, 'tasks');
    if (fs.existsSync(tasksDir)) {
      const files = fs.readdirSync(tasksDir);
      for (const file of files) {
        if (file.endsWith('.task.xml') || file.endsWith('.task.md')) {
          const name = file.replace(/\.(task\.xml|task\.md)$/, '');
          tasks.push({ module, name, path: path.join(tasksDir, file) });
        }
      }
    }
  }
  return tasks;
}

// Ensure directory exists
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// Create OpenCode agent launchers
function createOpenCodeAgents(agents) {
  const agentDir = path.join(projectDir, '.opencode/agent');
  ensureDir(agentDir);

  for (const agent of agents) {
    const content = `---
name: '${agent.name}'
description: 'BMAD ${agent.module.toUpperCase()} Agent: ${agent.name}'
mode: 'primary'
---

You must fully embody this agent's persona and follow all activation instructions exactly as specified. NEVER break character until given an exit command.

<agent-activation CRITICAL="TRUE">
1. LOAD the FULL agent file from @_bmad/modules/${agent.module}/agents/${agent.name}.agent.yaml
2. READ its entire contents - this contains the complete agent persona, menu, and instructions
3. FOLLOW every step in the <activation> section precisely
4. DISPLAY the welcome/greeting as instructed
5. PRESENT the numbered menu
6. WAIT for user input before proceeding
</agent-activation>
`;
    const filePath = path.join(agentDir, `bmad-agent-${agent.module}-${agent.name}.md`);
    fs.writeFileSync(filePath, content);
  }

  return agents.length;
}

// Create OpenCode workflow commands
function createOpenCodeWorkflows(workflows) {
  const commandDir = path.join(projectDir, '.opencode/command');
  ensureDir(commandDir);

  for (const workflow of workflows) {
    const content = fs.readFileSync(workflow.path, 'utf8');
    const filePath = path.join(commandDir, `bmad-${workflow.module}-${workflow.name}.md`);
    fs.writeFileSync(filePath, content);
  }

  return workflows.length;
}

// Create Gemini TOML commands
function createGeminiCommands(agents, workflows, tasks) {
  const commandDir = path.join(projectDir, '.gemini/commands');
  ensureDir(commandDir);

  // Agent commands
  for (const agent of agents) {
    const content = `description = "BMAD ${agent.module.toUpperCase()} Agent: ${agent.name}"
prompt = """
Activate BMAD agent '${agent.name}' from ${agent.module} module.

Load the agent file from @_bmad/modules/${agent.module}/agents/${agent.name}.agent.yaml and follow all activation instructions.
"""
`;
    const filePath = path.join(commandDir, `bmad-agent-${agent.module}-${agent.name}.toml`);
    fs.writeFileSync(filePath, content);
  }

  // Workflow commands
  for (const workflow of workflows) {
    const workflowContent = fs.readFileSync(workflow.path, 'utf8');
    const content = `description = "BMAD ${workflow.module.toUpperCase()} Workflow: ${workflow.name}"
prompt = """
${workflowContent}
"""
`;
    const filePath = path.join(commandDir, `bmad-workflow-${workflow.module}-${workflow.name}.toml`);
    fs.writeFileSync(filePath, content);
  }

  // Task commands
  for (const task of tasks) {
    const taskContent = fs.readFileSync(task.path, 'utf8');
    const content = `description = "BMAD ${task.module.toUpperCase()} Task: ${task.name}"
prompt = """
${taskContent}
"""
`;
    const filePath = path.join(commandDir, `bmad-task-${task.module}-${task.name}.toml`);
    fs.writeFileSync(filePath, content);
  }

  return agents.length + workflows.length + tasks.length;
}

// Main function
function main() {
  console.log('🚀 Starte manuelle BMAD IDE-Konfiguration...\n');

  // Collect artifacts
  console.log('📦 Sammle Agenten...');
  const agents = collectAgents();
  console.log(`   ✓ ${agents.length} Agenten gefunden`);

  console.log('📦 Sammle Workflows...');
  const workflows = collectWorkflows();
  console.log(`   ✓ ${workflows.length} Workflows gefunden`);

  console.log('📦 Sammle Tasks...');
  const tasks = collectTasks();
  console.log(`   ✓ ${tasks.length} Tasks gefunden\n`);

  // Setup OpenCode
  console.log('⚙️  Erstelle OpenCode-Konfiguration...');
  const openCodeAgents = createOpenCodeAgents(agents);
  const openCodeWorkflows = createOpenCodeWorkflows(workflows);
  console.log(`   ✓ ${openCodeAgents} Agenten nach .opencode/agent/`);
  console.log(`   ✓ ${openCodeWorkflows} Workflows nach .opencode/command/\n`);

  // Setup Gemini
  console.log('⚙️  Erstelle Gemini-Konfiguration...');
  const geminiCommands = createGeminiCommands(agents, workflows, tasks);
  console.log(`   ✓ ${geminiCommands} Befehle nach .gemini/commands/\n`);

  // Verification
  console.log('📊 Installations-Verifizierung:\n');
  console.log(`OpenCode Agenten: ${openCodeAgents}`);
  console.log(`OpenCode Workflows: ${openCodeWorkflows}`);
  console.log(`Gemini Befehle: ${geminiCommands}`);
  console.log(`loop.toml erhalten: ${fs.existsSync(path.join(projectDir, '.gemini/commands/loop.toml')) ? '✓' : '✗'}`);
  console.log(`loop.toml.backup: ${fs.existsSync(path.join(projectDir, '.gemini/commands/loop.toml.backup')) ? '✓' : '✗'}`);

  console.log('\n✨ Installation abgeschlossen!\n');
  console.log('📚 Weitere Informationen:\n');
  console.log('   OpenCode Agenten: .opencode/agent/');
  console.log('   OpenCode Befehle: .opencode/command/');
  console.log('   Gemini Befehle: .gemini/commands/\n');

  console.log('   In Gemini CLI nutzen:\n');
  console.log('     /bmad:agents:{module}:{agent-name}');
  console.log('     /bmad:workflows:{module}:{workflow-name}');
  console.log('     /bmad:tasks:{module}:{task-name}\n');

  console.log('   Beispiele:\n');
  console.log('     /bmad:agents:bmm:analyst');
  console.log('     /bmad:workflows:bmm:plan-project');
  console.log('     /bmad:tasks:core:brainstorming\n');
}

main();
