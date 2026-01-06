# Code-Mode MCP Server Setup

## Overview
The UTCP Code-Mode MCP server has been successfully configured and is ready to use. This server enables executing TypeScript code with direct access to registered APIs and tools.

## Configuration

### MCP Server Configuration
Location: `/home/kek/.var/app/com.vscodium.codium/config/VSCodium/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

Server name: `github.com/universal-tool-calling-protocol/code-mode`

The server runs via `npx @utcp/code-mode-mcp` and loads configuration from `/home/kek/.utcp_config.json`.

### UTCP Configuration
Location: `/home/kek/.utcp_config.json`

Currently configured with two HTTP API integrations:
- **OpenLibrary API**: 11 tools for searching books, authors, and library data
- **GitHub REST API**: 1078 tools for comprehensive GitHub operations

## How Code-Mode Works

Instead of making multiple sequential tool calls, Code-Mode allows you to write TypeScript code that chains multiple operations together:

### Traditional Approach (Multiple Round Trips)
```
1. Call tool: get_user_repos
2. Wait for response
3. Call tool: get_repo_issues  
4. Wait for response
5. Call tool: filter_issues
6. Wait for response
```

### Code-Mode Approach (Single Execution)
```typescript
const { result } = await call_tool_chain(`
  // Fetch repos
  const repos = await github_api.list_user_repos({ username: 'octocat' });
  
  // Get issues for first repo
  const issues = await github_api.list_repo_issues({ 
    owner: 'octocat', 
    repo: repos[0].name 
  });
  
  // Process and filter in-sandbox
  const criticalIssues = issues.filter(i => 
    i.labels.some(l => l.name === 'critical')
  );
  
  return {
    repo: repos[0].name,
    totalIssues: issues.length,
    criticalCount: criticalIssues.length
  };
`);
```

## Key Benefits

1. **Performance**: Single API call instead of multiple round-trips
2. **Efficiency**: Process data in-sandbox without bloating context
3. **Natural**: Write code instead of orchestrating tool calls
4. **Batching**: Chain multiple operations seamlessly

## Available Tools

The MCP server provides these management tools:

- `call_tool_chain` - Execute TypeScript code with tool access
- `search_tools` - Find tools by description
- `list_tools` - List all available tools
- `register_manual` - Add new API/tool integrations
- `deregister_manual` - Remove integrations
- `tool_info` - Get detailed tool information
- `get_required_keys_for_tool` - Check required environment variables

## Example Usage

Once the server is connected through MCP, you can use it like this:

### Search for Available Tools
```typescript
search_tools("search books by author")
// Returns tools from OpenLibrary like search_authors, search_books, etc.
```

### Execute Code with Multiple API Calls
```typescript
call_tool_chain(`
  // Search for books by Isaac Asimov
  const books = await openlibrary.search_books({
    author: "Isaac Asimov",
    limit: 5
  });
  
  console.log('Found', books.docs.length, 'books');
  
  // Return formatted results
  return books.docs.map(book => ({
    title: book.title,
    year: book.first_publish_year,
    isbn: book.isbn?.[0]
  }));
`)
```

## Adding More APIs

To add more tool integrations, edit `/home/kek/.utcp_config.json` and add entries to the `manual_call_templates` array:

```json
{
  "name": "your_api_name",
  "call_template_type": "http",
  "http_method": "GET",
  "url": "https://api.example.com/openapi.json",
  "content_type": "application/json"
}
```

The server will automatically reload and discover tools from the new API.

## Repository Location

The code-mode repository is cloned at: `/home/kek/socializer/code-mode/`

## Documentation

- Main README: `/home/kek/socializer/code-mode/README.md`
- MCP Server README: `/home/kek/socializer/code-mode/code-mode-mcp/README.md`
- Official docs: https://github.com/universal-tool-calling-protocol/code-mode

## Performance Benchmarks

According to independent studies, Code-Mode provides:
- **67% faster** for simple scenarios (2-3 tools)
- **75% faster** for medium complexity (4-7 tools)  
- **88% faster** for complex workflows (8+ tools)
- **$9,536/year savings** at 1,000 scenarios/day (at typical LLM pricing)

## Security Notes

- Code execution happens in isolated Node.js VM sandbox
- No direct filesystem access (unless explicitly configured)
- Timeout protection prevents runaway code
- CLI tools are disabled by default for security