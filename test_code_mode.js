#!/usr/bin/env node

/**
 * Test script for Code-Mode functionality
 * Demonstrates executing TypeScript code with tool access
 */

import { CodeModeUtcpClient } from '@utcp/code-mode';

async function testCodeMode() {
  console.log('🚀 Initializing Code-Mode UTCP Client...\n');
  
  try {
    // Create client with configuration from file
    const client = await CodeModeUtcpClient.create(process.cwd(), {
      load_variables_from: [
        {
          variable_loader_type: 'dotenv',
          env_file_path: '/home/kek/socializer/.env'
        }
      ],
      tool_repository: {
        tool_repository_type: 'in_memory'
      },
      tool_search_strategy: {
        tool_search_strategy_type: 'tag_and_description_word_match'
      },
      manual_call_templates: [
        {
          name: 'openlibrary',
          call_template_type: 'http',
          http_method: 'GET',
          url: 'https://openlibrary.org/static/openapi.json',
          content_type: 'application/json'
        }
      ],
      post_processing: []
    });
    
    console.log('✅ Client initialized successfully!\n');
    
    // Test 1: Search for available tools
    console.log('📚 Test 1: Searching for book-related tools...');
    const bookTools = await client.searchTools('search books');
    console.log(`Found ${bookTools.length} book-related tools:`);
    bookTools.slice(0, 5).forEach(tool => {
      console.log(`  - ${tool.name}: ${tool.description}`);
    });
    console.log('');
    
    // Test 2: List all available tools
    console.log('📋 Test 2: Listing all available tools...');
    const allToolNames = await client.listTools();
    console.log(`Total tools available: ${allToolNames.length}`);
    console.log('First 10 tools:', allToolNames.slice(0, 10).join(', '));
    console.log('');
    
    // Test 3: Execute TypeScript code with tool chaining
    console.log('🔧 Test 3: Executing TypeScript code with OpenLibrary API...');
    const { result, logs } = await client.callToolChain(`
      // Search for science fiction books
      const searchResult = await openlibrary.get_search({
        q: 'science fiction',
        limit: 3
      });
      
      console.log('API call successful!');
      console.log('Found', searchResult.numFound, 'total sci-fi books');
      
      // Process results in-sandbox
      const books = searchResult.docs.slice(0, 3).map(book => ({
        title: book.title,
        author: book.author_name?.[0] || 'Unknown',
        year: book.first_publish_year,
        isbn: book.isbn?.[0]
      }));
      
      return {
        totalFound: searchResult.numFound,
        sampledBooks: books
      };
    `, 30000);
    
    console.log('\n📊 Execution Results:');
    console.log('Logs:', logs);
    console.log('\nReturned Data:');
    console.log(JSON.stringify(result, null, 2));
    console.log('');
    
    // Test 4: Get TypeScript interfaces for tools
    console.log('🔍 Test 4: Generating TypeScript interfaces...');
    const interfaces = await client.getAllToolsTypeScriptInterfaces();
    console.log('Sample interface (first 500 chars):');
    console.log(interfaces.substring(0, 500) + '...\n');
    
    console.log('✨ All tests completed successfully!');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.stack) {
      console.error('\nStack trace:', error.stack);
    }
    process.exit(1);
  }
}

testCodeMode();