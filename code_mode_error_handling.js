#!/usr/bin/env node

/**
 * Enhanced Error Handling and Validation for Code-Mode
 * Provides better error messages and validation for common issues
 */

import { CodeModeUtcpClient } from '@utcp/code-mode';
import {
  VariableLoaderSerializer,
  ConcurrentToolRepositoryConfigSerializer,
  ToolSearchStrategyConfigSerializer,
  CallTemplateSerializer
} from '@utcp/sdk';
import { readFileSync, existsSync } from 'fs';

// Import required plugins
import '@utcp/dotenv-loader';
import '@utcp/http';

class CodeModeValidator {
  constructor() {
    this.errors = [];
    this.warnings = [];
  }

  // Validate configuration file exists and is readable
  validateConfigFile(configPath) {
    try {
      if (!existsSync(configPath)) {
        this.errors.push(`Configuration file not found: ${configPath}`);
        this.errors.push('Create .utcp_config.json in your working directory');
        return false;
      }

      const config = JSON.parse(readFileSync(configPath, 'utf-8'));
      console.log(` Configuration file loaded: ${configPath}`);
      return this.validateConfigStructure(config);
    } catch (error) {
      this.errors.push(`Invalid configuration file: ${error.message}`);
      return false;
    }
  }

  // Validate configuration structure
  validateConfigStructure(config) {
    let isValid = true;

    // Check required top-level properties
    const requiredProps = ['tool_repository', 'tool_search_strategy', 'manual_call_templates'];
    for (const prop of requiredProps) {
      if (!config[prop]) {
        this.errors.push(`Missing required property: ${prop}`);
        isValid = false;
      }
    }

    // Validate manual_call_templates
    if (config.manual_call_templates) {
      if (!Array.isArray(config.manual_call_templates)) {
        this.errors.push('manual_call_templates must be an array');
        isValid = false;
      } else if (config.manual_call_templates.length === 0) {
        this.warnings.push('No APIs configured in manual_call_templates');
      } else {
        // Validate each manual
        config.manual_call_templates.forEach((manual, index) => {
          if (!manual.name) {
            this.errors.push(`Manual ${index}: missing required 'name' property`);
            isValid = false;
          }
          if (!manual.call_template_type) {
            this.errors.push(`Manual ${manual.name || index}: missing required 'call_template_type' property`);
            isValid = false;
          } else if (!['http', 'mcp', 'text', 'file', 'cli'].includes(manual.call_template_type)) {
            this.warnings.push(`Manual ${manual.name}: unknown call_template_type '${manual.call_template_type}'`);
          }
        });
      }
    }

    return isValid;
  }

  // Validate environment and dependencies
  async validateEnvironment() {
    // Check for common plugin imports
    try {
      await import('@utcp/http');
      console.log(' HTTP plugin available');
    } catch (error) {
      this.warnings.push('HTTP plugin not imported. Add: import "@utcp/http";');
    }

    try {
      await import('@utcp/dotenv-loader');
      console.log(' Dotenv loader available');
    } catch (error) {
      this.warnings.push('Dotenv loader not imported. Add: import "@utcp/dotenv-loader";');
    }
  }

  // Create a client with enhanced error handling
  async createValidatedClient(configPath = '/home/kek/.utcp_config.json', rootDir = '/home/kek/socializer') {
    console.log('= Validating Code-Mode setup...\n');

    // Step 1: Validate configuration file
    if (!this.validateConfigFile(configPath)) {
      this.printValidationReport();
      throw new Error('Configuration validation failed');
    }

    // Step 2: Validate environment
    await this.validateEnvironment();

    // Step 3: Load and validate configuration
    const config = JSON.parse(readFileSync(configPath, 'utf-8'));

    // Step 4: Create properly typed configuration
    console.log('<×  Building typed configuration...');
    const typedConfig = {
      variables: config.variables || {},
      load_variables_from: config.load_variables_from ? config.load_variables_from.map(loader =>
        VariableLoaderSerializer.prototype.validateDict(loader)
      ) : null,
      tool_repository: ConcurrentToolRepositoryConfigSerializer.prototype.validateDict(config.tool_repository),
      tool_search_strategy: ToolSearchStrategyConfigSerializer.prototype.validateDict(config.tool_search_strategy),
      post_processing: config.post_processing || [],
      manual_call_templates: config.manual_call_templates.map(manual =>
        CallTemplateSerializer.prototype.validateDict(manual)
      )
    };

    // Step 5: Create client with error handling
    try {
      console.log('=€ Creating Code-Mode client...');
      const client = await CodeModeUtcpClient.create(rootDir, typedConfig);
      console.log(' Client created successfully!\n');

      this.printValidationReport();
      return client;
    } catch (error) {
      this.errors.push(`Client creation failed: ${error.message}`);
      this.printValidationReport();
      throw error;
    }
  }

  // Print validation report
  printValidationReport() {
    if (this.errors.length > 0) {
      console.log('L Validation Errors:');
      this.errors.forEach(error => console.log(`   " ${error}`));
      console.log('');
    }

    if (this.warnings.length > 0) {
      console.log('   Validation Warnings:');
      this.warnings.forEach(warning => console.log(`   " ${warning}`));
      console.log('');
    }

    if (this.errors.length === 0 && this.warnings.length === 0) {
      console.log(' No validation issues found!\n');
    }
  }

  // Test client functionality with enhanced error handling
  async testClientFunctionality(client) {
    console.log('>ê Testing client functionality...\n');

    const tests = [
      {
        name: 'Tool Discovery',
        test: async () => {
          const tools = await client.getTools();
          console.log(`   =Ê Found ${tools.length} tools`);
          return tools.length > 0;
        }
      },
      {
        name: 'Tool Search',
        test: async () => {
          const results = await client.searchTools('api');
          console.log(`   = Search returned ${results.length} results`);
          return true;
        }
      },
      {
        name: 'TypeScript Interface Generation',
        test: async () => {
          const interfaces = await client.getAllToolsTypeScriptInterfaces();
          console.log(`   =Ý Generated ${interfaces.length} characters of TypeScript interfaces`);
          return interfaces.length > 0;
        }
      },
      {
        name: 'Basic Code Execution',
        test: async () => {
          const { result, logs } = await client.callToolChain(`
            console.log('Test execution successful');
            return { status: 'ok', timestamp: Date.now() };
          `, 5000);
          console.log(`   =» Code execution returned: ${JSON.stringify(result)}`);
          return result && result.status === 'ok';
        }
      }
    ];

    let passed = 0;
    let failed = 0;

    for (const test of tests) {
      try {
        console.log(`Testing: ${test.name}`);
        const success = await test.test();
        if (success) {
          console.log(`    ${test.name} passed\n`);
          passed++;
        } else {
          console.log(`   L ${test.name} failed\n`);
          failed++;
        }
      } catch (error) {
        console.log(`   L ${test.name} failed: ${error.message}\n`);
        failed++;
        this.errors.push(`${test.name} test failed: ${error.message}`);
      }
    }

    console.log(`=È Test Results: ${passed} passed, ${failed} failed`);
    return failed === 0;
  }
}

// Enhanced error messages for common issues
class CodeModeErrorHandler {
  static getErrorMessage(error) {
    const errorStr = error.message || String(error);

    // Plugin-related errors
    if (errorStr.includes('Invalid variable_loader_type')) {
      return {
        title: 'Missing Plugin Import',
        message: 'You need to import the dotenv plugin',
        fix: 'Add this import at the top of your file:\nimport "@utcp/dotenv-loader";'
      };
    }

    if (errorStr.includes('Invalid call_template_type')) {
      return {
        title: 'Missing Protocol Plugin',
        message: 'You need to import the HTTP plugin for API calls',
        fix: 'Add this import at the top of your file:\nimport "@utcp/http";'
      };
    }

    // Configuration errors
    if (errorStr.includes('manual_call_templates must be an array')) {
      return {
        title: 'Invalid Configuration',
        message: 'manual_call_templates should be an array in your .utcp_config.json',
        fix: 'Check your configuration file format'
      };
    }

    if (errorStr.includes('Missing required property')) {
      return {
        title: 'Incomplete Configuration',
        message: 'Your .utcp_config.json is missing required properties',
        fix: 'Ensure tool_repository, tool_search_strategy, and manual_call_templates are defined'
      };
    }

    // Serialization errors
    if (errorStr.includes('Zod validation failed')) {
      return {
        title: 'Configuration Schema Error',
        message: 'Your configuration doesn\'t match the expected schema',
        fix: 'Use proper serializer methods: Serializer.prototype.validateDict(config)'
      };
    }

    // Default error
    return {
      title: 'Unknown Error',
      message: errorStr,
      fix: 'Check the error details and configuration'
    };
  }

  static printFriendlyError(error) {
    const errorInfo = this.getErrorMessage(error);

    console.log('\nL Code-Mode Error');
    console.log('P'.repeat(50));
    console.log(`=Ë ${errorInfo.title}`);
    console.log(`=¬ ${errorInfo.message}`);
    console.log(`=' Fix: ${errorInfo.fix}`);
    console.log('P'.repeat(50));
  }
}

// Demonstration script
async function demonstrateErrorHandling() {
  console.log('=á  Code-Mode Enhanced Error Handling & Validation Demo\n');

  const validator = new CodeModeValidator();

  try {
    // Test 1: Valid configuration
    console.log('Test 1: Valid Configuration');
    console.log(' '.repeat(40));

    const client = await validator.createValidatedClient('/home/kek/.utcp_config.json');

    // Test client functionality
    const allTestsPassed = await validator.testClientFunctionality(client);

    if (allTestsPassed) {
      console.log('<‰ All tests passed! Code-Mode is properly configured.\n');
    } else {
      console.log('   Some tests failed. Check the validation report above.\n');
    }

  } catch (error) {
    console.log('\n=¨ Configuration/Setup Error Detected:');
    CodeModeErrorHandler.printFriendlyError(error);
  }

  // Test 2: Demonstrate error handling with invalid config
  console.log('\nTest 2: Error Handling Examples');
  console.log(' '.repeat(40));

  // Simulate common errors
  const mockErrors = [
    new Error('Invalid variable_loader_type: dotenv'),
    new Error('Invalid call_template_type: http'),
    new Error('manual_call_templates must be an array'),
    new Error('Missing required property: tool_repository')
  ];

  mockErrors.forEach((error, index) => {
    console.log(`\nExample ${index + 1}:`);
    CodeModeErrorHandler.printFriendlyError(error);
  });

  console.log('\n( Error handling demonstration complete!');
  console.log('\n=¡ Benefits of Enhanced Error Handling:');
  console.log('   " Clear, actionable error messages');
  console.log('   " Specific fixes for common issues');
  console.log('   " Validation before client creation');
  console.log('   " Comprehensive testing of functionality');
}

// Run the demonstration
demonstrateErrorHandling().catch(error => {
  console.error('Demo failed:', error);
  CodeModeErrorHandler.printFriendlyError(error);
});