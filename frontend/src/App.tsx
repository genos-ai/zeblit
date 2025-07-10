import { Route, Switch, Redirect } from 'wouter'
import { AuthProvider } from './contexts/AuthContext'
import { WebSocketProvider } from './contexts/WebSocketContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { Dashboard } from './pages/Dashboard'
import { NewProject } from './pages/NewProject'
import { ProjectDetail } from './pages/ProjectDetail'
import './App.css'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <WebSocketProvider>
          <Switch>
            <Route path="/login" component={Login} />
            <Route path="/register" component={Register} />
            
            {/* Protected Routes */}
            <Route path="/dashboard">
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            </Route>
            
            {/* More specific route must come first */}
            <Route path="/projects/new">
              <ProtectedRoute>
                <NewProject />
              </ProtectedRoute>
            </Route>
            
            <Route path="/projects/:id">
              <ProtectedRoute>
                <ProjectDetail />
              </ProtectedRoute>
            </Route>
            
            {/* Default redirect */}
            <Route path="/">
              <Redirect to="/dashboard" />
            </Route>
          </Switch>
        </WebSocketProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
