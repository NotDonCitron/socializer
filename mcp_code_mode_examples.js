#!/usr/bin/env node

/**
 * MCP-Focused Code-Mode Examples
 * Demonstrates using Code-Mode through the MCP interface
 * These examples show how to interact with the working MCP server
 */

import { CodeModeUtcpClient } from '@utcp/code-mode';
import { readFileSync } from 'fs';

// Mock MCP client to simulate MCP protocol communication
class MockMCPClient {
  constructor() {
    this.tools = new Map();
    this.resources = new Map();
  }

  async initialize() {
    console.log('🔌 Connecting to Code-Mode MCP server...');

    // Load the config that the MCP server uses
    const config = JSON.parse(readFileSync('/home/kek/.utcp_config.json', 'utf-8'));
    console.log('📁 Loaded MCP server configuration');

    // Create client with same config as MCP server
    this.client = await CodeModeUtcpClient.create('/home/kek/socializer', {
      load_variables_from: null, // MCP server handles this
      tool_repository: { tool_repository_type: "in_memory" },
      tool_search_strategy: { tool_search_strategy_type: "tag_and_description_word_match" },
      post_processing: [],
      manual_call_templates: config.manual_call_templates,
      variables: {}
    });

    console.log('✅ MCP server connection established');
    return this;
  }

  // Simulate MCP tool calling
  async callTool(name, args) {
    console.log(`🔧 Calling MCP tool: ${name}`);
    console.log(`📝 Arguments:`, JSON.stringify(args, null, 2));

    try {
      const result = await this.client.callTool(name, args);
      console.log(`✅ Tool result:`, result);
      return { result };
    } catch (error) {
      console.error(`❌ Tool error:`, error.message);
      return { error: error.message };
    }
  }

  // Simulate MCP tool listing
  async listTools() {
    const tools = await this.client.getTools();
    return tools.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputs
    }));
  }

  // Simulate MCP tool search
  async searchTools(query) {
    const tools = await this.client.searchTools(query);
    return tools.map(tool => ({
      name: tool.name,
      description: tool.description
    }));
  }

  // Simulate MCP code execution (the main feature!)
  async callToolChain(code, timeout = 30000) {
    console.log('🚀 Executing TypeScript code via MCP call_tool_chain...');
    console.log('📄 Code to execute:');
    console.log(code);
    console.log('');

    const { result, logs } = await this.client.callToolChain(code, timeout);

    console.log('📊 Execution completed:');
    console.log('Result:', JSON.stringify(result, null, 2));
    console.log('Logs:', logs);
    console.log('');

    return { result, logs };
  }
}

async function demonstrateMCPExamples() {
  console.log('🎯 Code-Mode MCP Interface Examples\n');
  console.log('These examples show how to use Code-Mode through the MCP protocol\n');

  const mcpClient = await new MockMCPClient().initialize();

  try {
    // Example 1: List available tools (like MCP list_tools)
    console.log('📋 Example 1: Listing Available Tools (MCP list_tools)');
    console.log('─'.repeat(60));
    const tools = await mcpClient.listTools();
    console.log(`Found ${tools.length} tools:`);
    tools.slice(0, 5).forEach(tool => {
      console.log(`  • ${tool.name}: ${tool.description.substring(0, 60)}...`);
    });
    console.log('');

    // Example 2: Search for tools (like MCP search_tools)
    console.log('🔍 Example 2: Searching for Tools (MCP search_tools)');
    console.log('─'.repeat(60));
    const searchResults = await mcpClient.searchTools('search');
    console.log(`Found ${searchResults.length} tools matching 'search':`);
    searchResults.slice(0, 3).forEach(tool => {
      console.log(`  • ${tool.name}`);
    });
    console.log('');

    // Example 3: Tool information (like MCP tool_info)
    console.log('ℹ️  Example 3: Tool Information (MCP tool_info)');
    console.log('─'.repeat(60));
    const toolsList = await mcpClient.listTools();
    if (toolsList.length > 0) {
      const sampleTool = toolsList[0];
      console.log(`Tool: ${sampleTool.name}`);
      console.log(`Description: ${sampleTool.description}`);
      console.log(`Input Schema: ${JSON.stringify(sampleTool.inputSchema, null, 2)}`);
    }
    console.log('');

    // Example 4: Register manual (like MCP register_manual)
    console.log('📝 Example 4: Registering New Manual (MCP register_manual)');
    console.log('─'.repeat(60));
    console.log('Note: MCP register_manual would allow dynamic API registration');
    console.log('In this demo, APIs are pre-configured in .utcp_config.json');
    console.log('');

    // Example 5: The main feature - Code execution (MCP call_tool_chain)
    console.log('🚀 Example 5: Code Execution (MCP call_tool_chain) - The Main Feature!');
    console.log('─'.repeat(60));

    // Simple data processing
    await mcpClient.callToolChain(`
      console.log('🎯 Code-Mode executing TypeScript code!');

      // Process some data
      const books = [
        { title: '1984', author: 'George Orwell', year: 1949 },
        { title: 'Brave New World', author: 'Aldous Huxley', year: 1932 },
        { title: 'Fahrenheit 451', author: 'Ray Bradbury', year: 1953 }
      ];

      const classics = books.filter(book => book.year < 1950);
      const averageYear = books.reduce((sum, book) => sum + book.year, 0) / books.length;

      console.log('Filtered', classics.length, 'classic dystopian novels');
      console.log('Average publication year:', Math.round(averageYear));

      return {
        totalBooks: books.length,
        classicsCount: classics.length,
        averageYear: Math.round(averageYear),
        classics: classics.map(b => b.title)
      };
    `);

    // Example 6: Multi-step workflow in single execution
    console.log('🔄 Example 6: Multi-Step Workflow in Single Execution');
    console.log('─'.repeat(60));

    await mcpClient.callToolChain(`
      console.log('🔄 Executing multi-step workflow...');

      // Step 1: Data preparation
      const rawData = [
        { name: 'Alice', scores: [85, 92, 78] },
        { name: 'Bob', scores: [75, 88, 91] },
        { name: 'Charlie', scores: [95, 87, 93] }
      ];

      console.log('Step 1: Data prepared for', rawData.length, 'students');

      // Step 2: Processing
      const processed = rawData.map(student => ({
        ...student,
        average: student.scores.reduce((a, b) => a + b, 0) / student.scores.length,
        highest: Math.max(...student.scores),
        passed: student.scores.every(score => score >= 70)
      }));

      console.log('Step 2: Calculated averages and pass status');

      // Step 3: Analysis
      const classAverage = processed.reduce((sum, s) => sum + s.average, 0) / processed.length;
      const passRate = processed.filter(s => s.passed).length / processed.length * 100;

      console.log('Step 3: Completed class analysis');

      return {
        studentCount: processed.length,
        classAverage: Math.round(classAverage * 100) / 100,
        passRate: Math.round(passRate * 100) / 100 + '%',
        topPerformer: processed.reduce((top, s) => s.average > top.average ? s : top),
        summary: \`Class of \${processed.length} students with \${Math.round(passRate)}% pass rate\`
      };
    `);

    // Example 7: Error handling demonstration
    console.log('⚠️  Example 7: Error Handling in Code Execution');
    console.log('─'.repeat(60));

    await mcpClient.callToolChain(`
      console.log('⚠️  Testing error handling...');

      try {
        // This will work
        const data = [1, 2, 3];
        const sum = data.reduce((a, b) => a + b, 0);
        console.log('✅ Successful calculation:', sum);

        // This would cause an error if uncommented
        // const result = await someUndefinedFunction();

        console.log('✅ All operations completed successfully');
        return { success: true, sum: sum };

      } catch (error) {
        console.error('❌ Caught error:', error.message);
        return { success: false, error: error.message };
      }
    `);

    console.log('✨ All MCP Code-Mode examples completed successfully!');
    console.log('\n💡 Key Takeaways:');
    console.log('   • MCP server provides clean tool discovery interface');
    console.log('   • call_tool_chain enables complex multi-step workflows');
    console.log('   • Single API call replaces dozens of traditional tool calls');
    console.log('   • In-sandbox execution with proper error handling');
    console.log('   • Console logging for debugging and monitoring');

  } catch (error) {
    console.error('❌ MCP Example error:', error.message);
    if (error.stack) {
      console.error(error.stack);
    }
  }
}

// Import required plugins
import '@utcp/dotenv-loader';
import '@utcp/http';

// Run the examples
demonstrateMCPExamples();