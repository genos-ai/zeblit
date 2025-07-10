# MCP Server Setup for React Development - Cursor AI Instructions

## Context
I'm developing a React.js application and need to set up MCP (Model Context Protocol) servers to help with debugging, particularly for:
- Inspecting browser console errors in real-time
- Taking screenshots of my web application
- Monitoring network requests and React component errors
- Debugging React-specific issues

## Primary Goal
Please help me set up and configure the BrowserTools MCP Server, which provides comprehensive React debugging capabilities including console monitoring, screenshot capture, and performance analysis.

## Step-by-Step Setup Instructions

### 1. Initial Installation
First, help me install the BrowserTools MCP Server by running these commands in my project directory:

```bash
# Install the MCP server
npx @agentdeskai/browser-tools-mcp@latest

# Install the browser extension server
npx @agentdeskai/browser-tools-server@latest
```

### 2. Configuration Setup
Create or update the MCP configuration file at `.cursor/mcp.json` with the following content:

```json
{
  "mcpServers": {
    "browser-tools": {
      "command": "npx",
      "args": ["@agentdeskai/browser-tools-mcp@latest"]
    }
  }
}
```

### 3. Chrome Extension Installation
Guide me through installing the BrowserTools Chrome extension:
1. Open Chrome and navigate to the extension installation page
2. Ensure the extension is properly connected to the MCP server
3. Verify the extension icon appears in the Chrome toolbar

### 4. Verify Installation
Help me verify the installation by:
1. Restarting Cursor to load the new MCP configuration
2. Checking that the browser-tools server appears in Cursor's MCP server list
3. Testing basic functionality with a simple React component

## Usage Examples

Once set up, show me how to use the MCP server for common React debugging tasks:

### Example 1: Monitor Console Errors
```
"Check the browser console for any errors in my React app running on localhost:3000"
```

### Example 2: Capture Screenshots
```
"Take a screenshot of the current page showing the React component rendering issue"
```

### Example 3: Debug Network Requests
```
"Show me all failed API calls in the network tab for my React app"
```

### Example 4: Run Full Debugging Suite
```
"Run the debugger mode to analyze my React app's performance, accessibility, and SEO"
```

## Specific React Debugging Scenarios

Help me use the MCP server for these React-specific debugging needs:

1. **Component Rendering Issues**
   - Monitor console for React warnings about keys, props, or state
   - Capture screenshots of components in different states
   - Track component mount/unmount lifecycle events

2. **State Management Debugging**
   - Monitor Redux/Context API state changes in console
   - Track API calls triggered by state updates
   - Identify unnecessary re-renders

3. **Performance Optimization**
   - Run Lighthouse audits on React pages
   - Identify components causing performance bottlenecks
   - Monitor bundle size and loading times

4. **Error Boundary Testing**
   - Capture screenshots when errors occur
   - Monitor error boundaries catching component errors
   - Track error frequency and patterns

## Troubleshooting

If we encounter issues, help me troubleshoot:

1. **"Client Closed" Error**
   - On Windows, prefix commands with `cmd /c`
   - Ensure Node.js is installed in the Windows environment (not WSL)

2. **Extension Connection Issues**
   - Verify the extension is enabled in Chrome
   - Check that the MCP server is running
   - Restart both Cursor and Chrome if needed

3. **Screenshot Capture Problems**
   - Ensure the React app is running and accessible
   - Check Chrome permissions for the extension
   - Verify the screenshot directory has write permissions

## Advanced Configuration (Optional)

Once basic setup is working, help me explore advanced features:

1. **Multi-tab debugging** - Monitor multiple React app instances
2. **Custom screenshot settings** - Configure format, quality, and viewport
3. **Automated testing integration** - Connect with Jest/Cypress workflows
4. **Performance baseline tracking** - Set up performance monitoring over time

## Project-Specific Integration

My React project details:
- Framework: [React.js / Next.js / Gatsby - specify which]
- State management: [Redux / Context API / Zustand - specify which]
- Development server: [localhost:3000 or specify port]
- Key debugging needs: [List specific issues you're facing]

Please guide me through the setup process step by step, ensuring each component is properly configured before moving to the next. After setup, demonstrate how to use the MCP server to debug a real issue in my React application.

## Success Criteria

The setup is complete when:
1. ✅ BrowserTools MCP Server is installed and configured
2. ✅ Chrome extension is installed and connected
3. ✅ I can capture browser console logs in Cursor
4. ✅ I can take screenshots directly from Cursor
5. ✅ I can monitor network requests and React errors
6. ✅ I've successfully debugged at least one React issue using the tools

Please proceed with the installation and setup, explaining each step as we go.