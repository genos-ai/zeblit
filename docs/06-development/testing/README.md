# Testing Documentation

*Version: 1.0.0*  
*Author: Zeblit Development Team*

## Overview

This directory contains comprehensive testing documentation for the Zeblit AI Platform. The testing approach is designed to ensure system reliability, performance, and user experience across all platform components.

## Testing Documents

### 📋 [Comprehensive Test Plan](./comprehensive-test-plan.md)
**Primary testing document** - Systematic test plan organized by functional areas and complexity levels. Use this for structured testing campaigns and release validation.

**Covers:**
- 7 testing phases from basic operations to performance testing
- Detailed test cases with success criteria
- Prerequisites and setup instructions
- Issue tracking and progress monitoring

### 🧪 [Test Guide](./test-guide.md)
**Quick manual testing** - Immediate tests you can run to verify basic functionality is working.

**Covers:**
- Login flow verification
- Project creation workflow
- Agent chat system
- File operations
- Quick smoke tests

### 🎯 [Testing Strategy](./testing-strategy.md)
**Testing philosophy and approach** - High-level testing strategy, methodologies, and quality standards.

**Covers:**
- Testing principles and methodologies
- Test automation strategy
- Quality gates and acceptance criteria
- Testing environments and tools

## Current Testing Status

### ✅ **Completed (Phase 1)**
- Authentication system
- Project management (CRUD operations)
- File operations
- Basic agent chat functionality

### 🔄 **In Progress (Phase 2)**
- Container management testing
- OrbStack integration validation
- Container lifecycle operations

### ⏳ **Upcoming**
- Real-time features (WebSocket, console streaming)
- Task scheduling system
- Advanced agent workflows
- Error handling and edge cases
- Performance and scalability testing

## Quick Start Testing

### 1. Prerequisites
```bash
# Ensure backend is running
python start_backend.py --verbose

# Verify OrbStack is installed and running
docker version

# Check database connectivity
psql -d zeblit_db -c "SELECT COUNT(*) FROM users;"
```

### 2. Run Basic Smoke Tests
```bash
# Test CLI connectivity
zeblit --help

# Test authentication
zeblit list

# Test agent chat
zeblit chat agents
zeblit chat send "Hello! Test message."
```

### 3. For Comprehensive Testing
Follow the [Comprehensive Test Plan](./comprehensive-test-plan.md) starting with Phase 2 (Container Management).

## Testing Tools

### CLI Testing
- **Primary Interface**: `zeblit` command-line tool
- **Direct API**: `curl` commands for backend testing
- **Database**: `psql` queries for data verification

### Load Testing
- Custom Python scripts in `scripts/` directory
- Concurrent user simulation
- API endpoint stress testing

### Real-time Testing
- WebSocket test clients
- Browser developer tools
- Console streaming verification

## Issue Reporting

When reporting issues found during testing:

1. **Use the issue template** from the comprehensive test plan
2. **Include environment details** (OS, versions, configuration)
3. **Provide reproduction steps** with exact commands
4. **Attach logs and screenshots** when relevant
5. **Specify test phase and case** that failed

## Testing Best Practices

### Before Testing
- [ ] Ensure clean environment state
- [ ] Verify all prerequisites are met
- [ ] Check service health endpoints
- [ ] Clear any previous test data if needed

### During Testing
- [ ] Follow test cases exactly as documented
- [ ] Document any deviations or issues immediately
- [ ] Take screenshots/logs of failures
- [ ] Verify expected outcomes thoroughly

### After Testing
- [ ] Update test status in documentation
- [ ] Report all issues found
- [ ] Clean up test data
- [ ] Update test documentation if needed

## Quality Gates

### Phase Completion Criteria
- [ ] All test cases pass their success criteria
- [ ] No critical or high-severity issues remain open
- [ ] Performance metrics meet defined thresholds
- [ ] Documentation updated with any changes
- [ ] Regression testing confirms existing functionality intact

### Release Readiness
- [ ] Phases 1-4 completed successfully (core functionality)
- [ ] Critical user workflows tested end-to-end
- [ ] Performance testing shows acceptable response times
- [ ] Error handling gracefully manages failure scenarios
- [ ] Security testing completed (authentication, authorization)

---

## Next Steps

1. **Complete Phase 2**: Container management testing
2. **Implement Phase 3**: Real-time features validation
3. **Automate Testing**: Create automated test suites for regression testing
4. **Performance Baseline**: Establish performance benchmarks
5. **User Acceptance**: Conduct user testing sessions

For questions about testing procedures or to report issues, refer to the [debugging guide](../debugging/) or create an issue with detailed reproduction steps.
