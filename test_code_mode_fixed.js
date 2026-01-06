#!/usr/bin/env node

/**
 * Fixed test script for Code-Mode MCP server
 * Uses proper SDK types and serialization
 */

import { CodeModeUtcpClient } from '@utcp/code-mode';
import {
  VariableLoaderSerializer,
  ConcurrentToolRepositoryConfigSerializer,
  ToolSearchStrategyConfigSerializer,
  ToolPostProcessorConfigSerializer,
  CallTemplateSerializer
} from '@utcp/sdk';
// Import required plugins
import '@utcp/dotenv-loader';
import '@utcp/http';

async function testCodeMode() {
  console.log('🚀 Testing Code-Mode with Proper SDK Types...\n');

  try {
    // Create properly typed configuration objects
    console.log('⚙️  Building configuration with proper types...');

    const config = {
      variables: {},
      load_variables_from: [
        VariableLoaderSerializer.prototype.validateDict({
          variable_loader_type: "dotenv",
          env_file_path: "/home/kek/socializer/.env"
        })
      ],
      tool_repository: ConcurrentToolRepositoryConfigSerializer.prototype.validateDict({
        tool_repository_type: "in_memory"
      }),
      tool_search_strategy: ToolSearchStrategyConfigSerializer.prototype.validateDict({
        tool_search_strategy_type: "tag_and_description_word_match"
      }),
      post_processing: [],
      manual_call_templates: [
        CallTemplateSerializer.prototype.validateDict({
          name: "openlibrary",
          call_template_type: "http",
          http_method: "GET",
          url: "https://openlibrary.org/static/openapi.json",
          content_type: "application/json"
        })
      ]
    };

    console.log('✅ Configuration built successfully!\n');

    // Create client with properly typed config
    console.log('🏗️  Creating Code-Mode client...');
    const client = await CodeModeUtcpClient.create('/home/kek/socializer', config);
    console.log('✅ Client created successfully!\n');

    // Test basic functionality
    console.log('🔍 Testing basic tool discovery...');
    const allTools = await client.getTools();
    console.log(`Found ${allTools.length} tools total`);
    if (allTools.length > 0) {
      console.log('First 5 tools:', allTools.slice(0, 5).map(t => t.name));
    }
    console.log('');

    // Test search functionality
    console.log('🔍 Searching for tools...');
    const searchResults = await client.searchTools('search');
    console.log(`Found ${searchResults.length} tools matching 'search'`);
    if (searchResults.length > 0) {
      console.log('Sample tool:', searchResults[0].name);
    }
    console.log('');

    // Test TypeScript interface generation
    console.log('🔧 Generating TypeScript interfaces...');
    const interfaces = await client.getAllToolsTypeScriptInterfaces();
    console.log('Generated interfaces length:', interfaces.length);
    console.log('Sample interfaces (first 300 chars):');
    console.log(interfaces.substring(0, 300) + '...\n');

    // Test basic code execution (without external API calls)
    console.log('💻 Testing basic code execution...');
    const { result, logs } = await client.callToolChain(`
      // Test basic JavaScript execution
      console.log('Hello from Code-Mode!');
      const data = [1, 2, 3, 4, 5];
      const sum = data.reduce((a, b) => a + b, 0);
      const average = sum / data.length;

      console.log('Processed array of', data.length, 'numbers');

      return {
        sum: sum,
        average: average,
        count: data.length,
        message: 'Code execution successful!'
      };
    `, 10000);

    console.log('📊 Execution Results:');
    console.log('Result:', JSON.stringify(result, null, 2));
    console.log('Logs:', logs);
    console.log('');

    console.log('✨ Code-Mode programmatic API test completed successfully!');
    console.log('\n💡 Demonstrated:');
    console.log('   • Proper SDK type usage');
    console.log('   • Client creation with typed configuration');
    console.log('   • Tool discovery and search');
    console.log('   • TypeScript interface generation');
    console.log('   • Basic code execution in sandbox');
    console.log('   • Fix for programmatic API validation errors');

  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.stack) {
      console.error('\nStack trace:');
      console.error(error.stack);
    }
    process.exit(1);
  }
}

testCodeMode();