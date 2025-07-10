import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    // Navigate to dashboard (protected route)
    await page.goto('/dashboard')
    
    // Should redirect to login
    await expect(page).toHaveURL('/login')
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  })

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto('/login')
    
    // Fill in login form
    await page.getByPlaceholder('Enter your email').fill('user@zeblit.com')
    await page.getByPlaceholder('Enter your password').fill('password123')
    
    // Submit form
    await page.getByRole('button', { name: 'Sign in' }).click()
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByRole('heading', { name: 'Your Projects' })).toBeVisible()
    
    // Should show user email in header
    await expect(page.getByText('user@zeblit.com')).toBeVisible()
  })

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login')
    
    // Fill in login form with wrong password
    await page.getByPlaceholder('Enter your email').fill('user@zeblit.com')
    await page.getByPlaceholder('Enter your password').fill('wrongpassword')
    
    // Submit form
    await page.getByRole('button', { name: 'Sign in' }).click()
    
    // Should show error message
    await expect(page.getByText('Invalid email or password')).toBeVisible()
    
    // Should stay on login page
    await expect(page).toHaveURL('/login')
  })

  test('should logout successfully', async ({ page }) => {
    // First login
    await page.goto('/login')
    await page.getByPlaceholder('Enter your email').fill('user@zeblit.com')
    await page.getByPlaceholder('Enter your password').fill('password123')
    await page.getByRole('button', { name: 'Sign in' }).click()
    
    // Wait for dashboard
    await expect(page).toHaveURL('/dashboard')
    
    // Click user menu
    await page.getByRole('button', { name: 'user@zeblit.com' }).click()
    
    // Click logout
    await page.getByRole('button', { name: 'Logout' }).click()
    
    // Should redirect to login
    await expect(page).toHaveURL('/login')
    
    // Try to access protected route
    await page.goto('/dashboard')
    
    // Should redirect back to login
    await expect(page).toHaveURL('/login')
  })

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login')
    
    // Click register link
    await page.getByText("Don't have an account? Sign up").click()
    
    // Should navigate to register page
    await expect(page).toHaveURL('/register')
    await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible()
  })
}) 