// Automated Code Review Scripts for Code-Mode
// Comprehensive analysis for Python/JavaScript codebases

function performCodeReview(codeSnippets, language = 'python') {
  const review = {
    summary: {
      totalFiles: codeSnippets.length,
      issuesFound: 0,
      criticalIssues: 0,
      warnings: 0,
      suggestions: 0
    },
    files: [],
    overallRecommendations: []
  };

  codeSnippets.forEach((code, index) => {
    const fileReview = analyzeFile(code, language, index);
    review.files.push(fileReview);
    review.summary.issuesFound += fileReview.issues.length;
    review.summary.criticalIssues += fileReview.issues.filter(i => i.severity === 'critical').length;
    review.summary.warnings += fileReview.issues.filter(i => i.severity === 'warning').length;
    review.summary.suggestions += fileReview.issues.filter(i => i.severity === 'suggestion').length;
  });

  // Generate overall recommendations
  if (review.summary.criticalIssues > 0) {
    review.overallRecommendations.push('Address critical issues before merging');
  }
  if (review.summary.issuesFound > review.summary.totalFiles * 2) {
    review.overallRecommendations.push('Consider refactoring - high issue density detected');
  }

  return review;
}

function analyzeFile(code, language, fileIndex) {
  const issues = [];
  const lines = code.split('\n');

  // Language-specific analysis
  if (language === 'python') {
    issues.push(...analyzePythonCode(code, lines, fileIndex));
  } else if (language === 'javascript') {
    issues.push(...analyzeJavaScriptCode(code, lines, fileIndex));
  }

  // General code analysis
  issues.push(...analyzeGeneralCode(code, lines, fileIndex));

  return {
    fileIndex,
    language,
    lines: lines.length,
    issues: issues.sort((a, b) => {
      const severityOrder = { critical: 3, warning: 2, suggestion: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    })
  };
}

function analyzePythonCode(code, lines, fileIndex) {
  const issues = [];

  // Check for long functions
  const functions = code.match(/def \w+\([^)]*\):/g) || [];
  if (functions.length > 15) {
    issues.push({
      type: 'complexity',
      severity: 'warning',
      line: 'multiple',
      message: `High function count (${functions.length}) - consider splitting into multiple files`,
      suggestion: 'Break down into smaller modules'
    });
  }

  // Check for bare except clauses
  if (code.includes('except:')) {
    issues.push({
      type: 'error-handling',
      severity: 'critical',
      line: 'multiple',
      message: 'Bare except clause found - too broad exception handling',
      suggestion: 'Specify exception types: except ValueError: or except Exception:'
    });
  }

  // Check for print statements in production code
  const printStatements = lines.filter(line => line.includes('print(') && !line.trim().startsWith('#'));
  if (printStatements.length > 0) {
    issues.push({
      type: 'debugging',
      severity: 'warning',
      line: 'multiple',
      message: `${printStatements.length} print statements found - remove for production`,
      suggestion: 'Use logging module instead: import logging; logging.info()'
    });
  }

  // Check for TODO comments
  const todos = lines.filter(line => line.includes('TODO') || line.includes('FIXME'));
  if (todos.length > 0) {
    issues.push({
      type: 'documentation',
      severity: 'suggestion',
      line: 'multiple',
      message: `${todos.length} TODO/FIXME comments found`,
      suggestion: 'Address or remove TODO comments before merging'
    });
  }

  return issues;
}

function analyzeJavaScriptCode(code, lines, fileIndex) {
  const issues = [];

  // Check for console.log statements
  const consoleLogs = lines.filter(line => line.includes('console.log') && !line.trim().startsWith('//'));
  if (consoleLogs.length > 0) {
    issues.push({
      type: 'debugging',
      severity: 'warning',
      line: 'multiple',
      message: `${consoleLogs.length} console.log statements found - remove for production`,
      suggestion: 'Use proper logging library or remove debug statements'
    });
  }

  // Check for var declarations (prefer let/const)
  const varDeclarations = lines.filter(line => line.includes('var '));
  if (varDeclarations.length > 0) {
    issues.push({
      type: 'modern-js',
      severity: 'suggestion',
      line: 'multiple',
      message: `${varDeclarations.length} var declarations found`,
      suggestion: 'Use let/const instead of var for better scoping'
    });
  }

  return issues;
}

function analyzeGeneralCode(code, lines, fileIndex) {
  const issues = [];

  // Check for very long lines
  const longLines = lines.filter(line => line.length > 100);
  if (longLines.length > 0) {
    issues.push({
      type: 'readability',
      severity: 'suggestion',
      line: 'multiple',
      message: `${longLines.length} lines exceed 100 characters`,
      suggestion: 'Break long lines for better readability'
    });
  }

  // Check for empty catch blocks
  if (code.includes('catch') && code.includes('{}')) {
    issues.push({
      type: 'error-handling',
      severity: 'warning',
      line: 'multiple',
      message: 'Empty catch block found',
      suggestion: 'Add proper error handling in catch blocks'
    });
  }

  return issues;
}

// Usage with Code-Mode:
/*
// Analyze Python codebase
const pythonFiles = ['radar/cli.py', 'radar/config.py', 'tests/test_cli.py'];
const review = performCodeReview(pythonFiles.map(file => readFile(file)), 'python');

// Analyze JavaScript codebase
const jsFiles = ['site/src/**/*.js', 'socializer-api/**/*.js'];
const jsReview = performCodeReview(jsFiles.map(file => readFile(file)), 'javascript');
*/

module.exports = {
  performCodeReview,
  analyzeFile,
  analyzePythonCode,
  analyzeJavaScriptCode,
  analyzeGeneralCode
};