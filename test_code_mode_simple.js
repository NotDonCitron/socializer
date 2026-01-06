#!/usr/bin/env node

/**
 * Simplified test script for Code-Mode MCP server
 * Tests basic functionality without complex registration
 */

import { CodeModeUtcpClient } from '@utcp/code-mode';

async function testCodeMode() {
  console.log('🚀 Testing Code-Mode UTCP Client...\n');

  try {
    // Try to create client with the config file
    console.log('⚙️  Creating Code-Mode client with config...');
    const client = await CodeModeUtcpClient.create('/home/kek/socializer', {
      load_variables_from: [
        {
          variable_loader_type: "dotenv",
          env_file_path: "/home/kek/socializer/.env"
        }
      ],
      tool_repository: {
        tool_repository_type: "in_memory"
      },
      tool_search_strategy: {
        tool_search_strategy_type: "tag_and_description_word_match"
      },
      manual_call_templates: [
        {
          name: "openlibrary",
          call_template_type: "http",
          http_method: "GET",
          url: "https://openlibrary.org/static/openapi.json",
          content_type: "application/json"
        }
      ],
      post_processing: []
    });
    console.log('✅ Client created successfully!\n');

    // Test basic functionality
    console.log('🔍 Testing basic tool discovery...');
    const allTools = await client.listTools();
    console.log(`Found ${allTools.length} tools total`);
    console.log('First 5 tools:', allTools.slice(0, 5));
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
    console.log('Sample interfaces (first 200 chars):');
    console.log(interfaces.substring(0, 200) + '...\n');

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

    console.log('✨ Basic Code-Mode test completed successfully!');
    console.log('\n💡 Demonstrated:');
    console.log('   • Client creation with configuration');
    console.log('   • Tool discovery and search');
    console.log('   • TypeScript interface generation');
    console.log('   • Basic code execution in sandbox');

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