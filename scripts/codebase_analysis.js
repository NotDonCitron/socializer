// Code-Mode Codebase Analysis Scripts
// Run these with Code-Mode for automated analysis

function analyzePythonCodebase(codeSnippets) {
  const analysis = {
    totalFiles: codeSnippets.length,
    complexity: {},
    patterns: {},
    recommendations: []
  };

  codeSnippets.forEach((code, index) => {
    // Analyze function complexity
    const functions = code.match(/def \w+\([^)]*\):/g) || [];
    const classes = code.match(/class \w+.*:/g) || [];
    const imports = code.match(/^(?:from \w+|import \w+)/gm) || [];

    analysis.complexity[`file_${index}`] = {
      functions: functions.length,
      classes: classes.length,
      imports: imports.length,
      lines: code.split('\n').length
    };

    // Check for code smells
    if (code.includes('TODO') || code.includes('FIXME')) {
      analysis.recommendations.push(`File ${index}: Remove TODO/FIXME comments`);
    }
    if (code.includes('print(') && !code.includes('# Debug')) {
      analysis.recommendations.push(`File ${index}: Remove debug print statements`);
    }
    if (functions.length > 10) {
      analysis.recommendations.push(`File ${index}: Consider breaking down large files (${functions.length} functions)`);
    }
  });

  return analysis;
}

function analyzeTestCoverage(testResults) {
  const coverage = {
    totalTests: testResults.length,
    passed: testResults.filter(t => t.status === 'passed').length,
    failed: testResults.filter(t => t.status === 'failed').length,
    skipped: testResults.filter(t => t.status === 'skipped').length,
    coverage: 0, // Would be calculated from coverage reports
    recommendations: []
  };

  coverage.passRate = ((coverage.passed / coverage.totalTests) * 100).toFixed(1) + '%';

  if (coverage.failed > 0) {
    coverage.recommendations.push(`Fix ${coverage.failed} failing tests`);
  }
  if (coverage.coverage < 80) {
    coverage.recommendations.push('Improve test coverage above 80%');
  }

  return coverage;
}

function analyzeDependencies(deps) {
  const analysis = {
    total: deps.length,
    outdated: deps.filter(d => d.outdated).length,
    vulnerable: deps.filter(d => d.vulnerable).length,
    byType: deps.reduce((acc, dep) => {
      const type = dep.version.startsWith('^') ? 'caret' :
                  dep.version.startsWith('~') ? 'tilde' : 'exact';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {}),
    recommendations: []
  };

  if (analysis.outdated > 0) {
    analysis.recommendations.push(`Update ${analysis.outdated} outdated dependencies`);
  }
  if (analysis.vulnerable > 0) {
    analysis.recommendations.push(`Fix ${analysis.vulnerable} security vulnerabilities`);
  }

  return analysis;
}

// Usage examples:
/*
// Analyze Python files
const pythonAnalysis = analyzePythonCodebase(pythonCodeSnippets);

// Analyze test results
const testAnalysis = analyzeTestCoverage(testResults);

// Analyze dependencies
const depAnalysis = analyzeDependencies(dependencies);
*/

module.exports = {
  analyzePythonCodebase,
  analyzeTestCoverage,
  analyzeDependencies
};