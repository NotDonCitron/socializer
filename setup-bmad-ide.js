const path = require('node:path');
const fs = require('fs-extra');
const chalk = require('chalk');

// Add BMAD source to Node path
const bmadSource = path.join(__dirname, 'socializer/BMAD-METHOD');
require.paths.unshift(path.join(bmadSource, 'tools/cli'));

const { AgentCommandGenerator } = require(`${bmadSource}/tools/cli/installers/lib/ide/shared/agent-command-generator`);
const { WorkflowCommandGenerator } = require(`${bmadSource}/tools/cli/installers/lib/ide/shared/workflow-command-generator`);
const { TaskToolCommandGenerator } = require(`${bmadSource}/tools/cli/installers/lib/ide/shared/task-tool-command-generator`);
const { OpenCodeSetup } = require(`${bmadSource}/tools/cli/installers/lib/ide/opencode`);
const { GeminiSetup } = require(`${bmadSource}/tools/cli/installers/lib/ide/gemini`);

const bmadDir = path.join(__dirname, '_bmad');
const projectDir = __dirname;
const selectedModules = ['bmm', 'bmb', 'cis', 'core'];

async function main() {
  console.log(chalk.cyan('🚀 Manuelle BMAD IDE-Konfiguration wird gestartet...\n'));

  // Setup OpenCode
  const openCode = new OpenCodeSetup();
  openCode.setBmadFolderName('_bmad');

  try {
    console.log(chalk.yellow('Setup OpenCode...'));
    const openCodeResult = await openCode.setup(projectDir, bmadDir, { selectedModules });
    console.log(chalk.green(`✓ OpenCode konfiguriert: ${openCodeResult.agents} agents, ${openCodeResult.workflows} workflows\n`));
  } catch (error) {
    console.error(chalk.red(`✗ OpenCode-Setup fehlgeschlagen: ${error.message}\n`));
  }

  // Setup Gemini
  const gemini = new GeminiSetup();
  gemini.setBmadFolderName('_bmad');

  try {
    console.log(chalk.yellow('Setup Gemini CLI...'));
    const geminiResult = await gemini.setup(projectDir, bmadDir, { selectedModules });
    console.log(chalk.green(`✓ Gemini konfiguriert: ${geminiResult.agents} agents, ${geminiResult.tasks} tasks, ${geminiResult.workflows} workflows\n`));
  } catch (error) {
    console.error(chalk.red(`✗ Gemini-Setup fehlgeschlagen: ${error.message}\n`));
  }

  // Verify installations
  console.log(chalk.cyan('\n📊 Installations-Verifizierung:\n'));

  const openCodeAgents = await fs.readdir(path.join(projectDir, '.opencode/agent')).then(files => files.filter(f => f.startsWith('bmad-')).length).catch(() => 0);
  const openCodeCommands = await fs.readdir(path.join(projectDir, '.opencode/command')).then(files => files.filter(f => f.startsWith('bmad-')).length).catch(() => 0);
  const geminiCommands = await fs.readdir(path.join(projectDir, '.gemini/commands')).then(files => files.filter(f => f.startsWith('bmad-')).length).catch(() => 0);

  console.log(chalk.dim(`OpenCode Agenten: ${openCodeAgents}`));
  console.log(chalk.dim(`OpenCode Befehle: ${openCodeCommands}`));
  console.log(chalk.dim(`Gemini Befehle: ${geminiCommands}`));
  console.log(chalk.dim(`Gemini loop.toml (erhalten): ${(await fs.pathExists(path.join(projectDir, '.gemini/commands/loop.toml'))) ? '✓' : '✗'}`));

  console.log(chalk.green('\n✨ Installation abgeschlossen!\n'));
}

main().catch(console.error);
