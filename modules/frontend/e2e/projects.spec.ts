import { test, expect } from '@playwright/test'

test.describe('Project Management', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('Enter your email').fill('user@zeblit.com')
    await page.getByPlaceholder('Enter your password').fill('password123')
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL('/dashboard')
  })

  test('should display project list on dashboard', async ({ page }) => {
    // Should show projects heading
    await expect(page.getByRole('heading', { name: 'Your Projects' })).toBeVisible()
    
    // Should show create new project button
    await expect(page.getByRole('button', { name: 'Create New Project' })).toBeVisible()
    
    // Should show existing projects (if any)
    const projectCards = page.locator('[data-testid="project-card"]')
    const count = await projectCards.count()
    
    if (count > 0) {
      // Check first project has required elements
      const firstProject = projectCards.first()
      await expect(firstProject.locator('h3')).toBeVisible() // Project name
      await expect(firstProject.locator('p')).toBeVisible() // Description
    }
  })

  test('should create new project through wizard', async ({ page }) => {
    // Click create new project
    await page.getByRole('button', { name: 'Create New Project' }).click()
    
    // Should navigate to new project wizard
    await expect(page).toHaveURL('/projects/new')
    await expect(page.getByRole('heading', { name: 'Create New Project' })).toBeVisible()
    
    // Step 1: Select template
    await expect(page.getByText('Step 1 of 3')).toBeVisible()
    await expect(page.getByText('Choose a Template')).toBeVisible()
    
    // Select Web Application template
    await page.getByText('Web Application').click()
    await page.getByRole('button', { name: 'Next' }).click()
    
    // Step 2: Project details
    await expect(page.getByText('Step 2 of 3')).toBeVisible()
    await expect(page.getByText('Project Details')).toBeVisible()
    
    // Fill in project details
    const timestamp = Date.now()
    const projectName = `test-project-${timestamp}`
    await page.getByPlaceholder('Enter project name').fill(projectName)
    await page.getByPlaceholder('Describe your project').fill('E2E test project')
    
    // Keep private selected
    await page.getByRole('button', { name: 'Next' }).click()
    
    // Step 3: Review
    await expect(page.getByText('Step 3 of 3')).toBeVisible()
    await expect(page.getByText('Review & Create')).toBeVisible()
    
    // Verify details
    await expect(page.getByText(projectName)).toBeVisible()
    await expect(page.getByText('E2E test project')).toBeVisible()
    await expect(page.getByText('Web Application')).toBeVisible()
    
    // Create project
    await page.getByRole('button', { name: 'Create Project' }).click()
    
    // Should redirect to project detail page
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/)
    
    // Should show project IDE interface
    await expect(page.locator('.monaco-editor')).toBeVisible()
  })

  test('should navigate to project detail page', async ({ page }) => {
    // Wait for projects to load
    await page.waitForSelector('[data-testid="project-card"]', { timeout: 10000 })
    
    // Click on first project
    const firstProject = page.locator('[data-testid="project-card"]').first()
    await firstProject.click()
    
    // Should navigate to project detail
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/)
    
    // Should show main IDE components
    await expect(page.locator('.monaco-editor')).toBeVisible() // Code editor
    await expect(page.getByText('Agent Chat')).toBeVisible() // Agent chat panel
    await expect(page.getByText('Preview')).toBeVisible() // Preview panel
    
    // Should show agent tabs at bottom
    await expect(page.getByText('Dev Manager')).toBeVisible()
    await expect(page.getByText('Product Manager')).toBeVisible()
    await expect(page.getByText('Engineer')).toBeVisible()
  })

  test('should toggle panels in project IDE', async ({ page }) => {
    // Navigate to first project
    await page.locator('[data-testid="project-card"]').first().click()
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/)
    
    // Test left panel (Agent Chat) collapse
    const leftCollapseButton = page.locator('button[aria-label="Collapse left panel"]').first()
    await leftCollapseButton.click()
    
    // Panel should be collapsed
    await expect(page.getByText('Agent Chat')).not.toBeVisible()
    
    // Expand again
    const leftExpandButton = page.locator('button[aria-label="Expand left panel"]').first()
    await leftExpandButton.click()
    await expect(page.getByText('Agent Chat')).toBeVisible()
    
    // Test right panel (Preview) collapse
    const rightCollapseButton = page.locator('button[aria-label="Collapse right panel"]').first()
    await rightCollapseButton.click()
    
    // Panel should be collapsed
    await expect(page.getByText('Preview')).not.toBeVisible()
    
    // Expand again
    const rightExpandButton = page.locator('button[aria-label="Expand right panel"]').first()
    await rightExpandButton.click()
    await expect(page.getByText('Preview')).toBeVisible()
  })
}) 