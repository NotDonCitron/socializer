// Dependency Management Scripts for Code-Mode
// Analyze and optimize Python/JavaScript dependencies

function analyzeDependencies(dependencies, language = 'python') {
  const analysis = {
    summary: {
      total: dependencies.length,
      outdated: 0,
      vulnerable: 0,
      deprecated: 0,
      recommendations: []
    },
    security: {},
    maintenance: {},
    optimization: {}
  };

  // Analyze each dependency
  dependencies.forEach(dep => {
    if (dep.outdated) analysis.summary.outdated++;
    if (dep.vulnerable) analysis.summary.vulnerable++;
    if (dep.deprecated) analysis.summary.deprecated++;
  });

  // Security Analysis
  analysis.security = analyzeSecurityIssues(dependencies);

  // Maintenance Analysis
  analysis.maintenance = analyzeMaintenanceBurden(dependencies, language);

  // Optimization Analysis
  analysis.optimization = analyzeOptimizationOpportunities(dependencies);

  // Generate Recommendations
  analysis.summary.recommendations = generateDependencyRecommendations(analysis);

  return analysis;
}

function analyzeSecurityIssues(dependencies) {
  const security = {
    critical: dependencies.filter(d => d.vulnerable && d.severity === 'critical').length,
    high: dependencies.filter(d => d.vulnerable && d.severity === 'high').length,
    medium: dependencies.filter(d => d.vulnerable && d.severity === 'medium').length,
    low: dependencies.filter(d => d.vulnerable && d.severity === 'low').length,
    totalVulnerabilities: 0,
    affectedPackages: [],
    recommendations: []
  };

  security.totalVulnerabilities = security.critical + security.high + security.medium + security.low;
  security.affectedPackages = dependencies.filter(d => d.vulnerable).map(d => d.name);

  if (security.critical > 0) {
    security.recommendations.push('URGENT: Update critical security vulnerabilities immediately');
  }
  if (security.high > 0) {
    security.recommendations.push('HIGH PRIORITY: Address high-severity security issues');
  }

  return security;
}

function analyzeMaintenanceBurden(dependencies, language) {
  const maintenance = {
    versionTypes: {},
    updateFrequency: {},
    maintainerActivity: {},
    recommendations: []
  };

  // Analyze version pinning patterns
  maintenance.versionTypes = dependencies.reduce((acc, dep) => {
    let type = 'exact';
    if (language === 'python') {
      if (dep.version.includes('>=')) type = 'minimum';
      else if (dep.version.includes('~=')) type = 'compatible';
      else if (dep.version.includes('==')) type = 'exact';
    } else if (language === 'javascript') {
      if (dep.version.startsWith('^')) type = 'caret';
      else if (dep.version.startsWith('~')) type = 'tilde';
      else type = 'exact';
    }
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});

  // Check for overly restrictive versioning
  const exactVersions = maintenance.versionTypes.exact || 0;
  if (exactVersions > dependencies.length * 0.7) {
    maintenance.recommendations.push('Use more flexible version ranges to allow compatible updates');
  }

  return maintenance;
}

function analyzeOptimizationOpportunities(dependencies) {
  const optimization = {
    unused: [],
    duplicates: {},
    heavyPackages: [],
    alternatives: [],
    recommendations: []
  };

  // Identify potentially heavy packages
  optimization.heavyPackages = dependencies
    .filter(d => d.size && d.size > 10 * 1024 * 1024) // > 10MB
    .map(d => ({ name: d.name, size: (d.size / 1024 / 1024).toFixed(1) + 'MB' }));

  // Check for common optimization opportunities
  const packageNames = dependencies.map(d => d.name.toLowerCase());

  if (packageNames.includes('lodash') && !packageNames.includes('lodash-es')) {
    optimization.alternatives.push('Consider lodash-es for smaller bundle size');
  }

  if (packageNames.includes('moment') && !packageNames.includes('dayjs')) {
    optimization.alternatives.push('Consider dayjs as a lighter moment.js alternative');
  }

  if (optimization.heavyPackages.length > 0) {
    optimization.recommendations.push(`Review ${optimization.heavyPackages.length} large packages for optimization`);
  }

  return optimization;
}

function generateDependencyRecommendations(analysis) {
  const recommendations = [];

  // Security recommendations
  if (analysis.security.critical > 0) {
    recommendations.push(`🚨 CRITICAL: Update ${analysis.security.critical} packages with critical vulnerabilities`);
  }

  if (analysis.security.high > 0) {
    recommendations.push(`⚠️ HIGH: Address ${analysis.security.high} high-severity security issues`);
  }

  // Maintenance recommendations
  if (analysis.maintenance.versionTypes.exact > analysis.summary.total * 0.8) {
    recommendations.push('Use flexible version ranges (^ for npm, ~= for pip) to allow compatible updates');
  }

  // Optimization recommendations
  if (analysis.optimization.heavyPackages.length > 0) {
    recommendations.push(`Optimize bundle size - review ${analysis.optimization.heavyPackages.length} large packages`);
  }

  // Outdated packages
  if (analysis.summary.outdated > 0) {
    recommendations.push(`Update ${analysis.summary.outdated} outdated dependencies`);
  }

  return recommendations;
}

function generateSecurityReport(dependencies) {
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalDependencies: dependencies.length,
      vulnerable: dependencies.filter(d => d.vulnerable).length,
      critical: dependencies.filter(d => d.vulnerable && d.severity === 'critical').length,
      high: dependencies.filter(d => d.vulnerable && d.severity === 'high').length
    },
    vulnerabilities: dependencies
      .filter(d => d.vulnerable)
      .map(d => ({
        package: d.name,
        version: d.version,
        severity: d.severity,
        description: d.vulnerabilityDescription,
        cve: d.cve || 'N/A'
      })),
    recommendations: []
  };

  if (report.summary.critical > 0) {
    report.recommendations.push('Immediate action required for critical vulnerabilities');
  }

  return report;
}

// Usage with Code-Mode:
/*
// Analyze Python requirements
const pythonDeps = parseRequirementsTxt('requirements.txt');
const pythonAnalysis = analyzeDependencies(pythonDeps, 'python');

// Analyze JavaScript packages
const jsDeps = parsePackageJson('package.json');
const jsAnalysis = analyzeDependencies(jsDeps, 'javascript');

// Generate security report
const securityReport = generateSecurityReport(allDeps);
*/

module.exports = {
  analyzeDependencies,
  analyzeSecurityIssues,
  analyzeMaintenanceBurden,
  analyzeOptimizationOpportunities,
  generateDependencyRecommendations,
  generateSecurityReport
};