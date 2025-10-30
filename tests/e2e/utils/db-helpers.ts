/**
 * Database Helper Functions for E2E Tests
 *
 * Provides utilities for verifying database state in E2E tests.
 * Requires DATABASE_URL environment variable to be set.
 */

import axios from 'axios';

/**
 * Query the backend API to get week information
 */
export async function getWeekInfo(weekId: number, baseUrl: string = 'http://localhost:8000'): Promise<any> {
  try {
    const response = await axios.get(`${baseUrl}/api/weeks/${weekId}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to get week info for week ${weekId}:`, error);
    throw error;
  }
}

/**
 * Query the backend API to get all weeks
 */
export async function getWeeks(year: number, baseUrl: string = 'http://localhost:8000'): Promise<any[]> {
  try {
    const response = await axios.get(`${baseUrl}/api/weeks`, {
      params: { year, include_metadata: true }
    });
    return response.data;
  } catch (error) {
    console.error(`Failed to get weeks for year ${year}:`, error);
    throw error;
  }
}

/**
 * Query the backend API to get import history
 */
export async function getImportHistory(baseUrl: string = 'http://localhost:8000'): Promise<any[]> {
  try {
    const response = await axios.get(`${baseUrl}/api/import/history`);
    return response.data;
  } catch (error) {
    console.error('Failed to get import history:', error);
    throw error;
  }
}

/**
 * Verify that player data was imported correctly
 */
export async function verifyPlayerCount(
  weekId: number,
  expectedCount: number,
  source: string,
  baseUrl: string = 'http://localhost:8000'
): Promise<{ actual: number; expected: number; matches: boolean }> {
  try {
    // Get week info which may include player count
    const weekInfo = await getWeekInfo(weekId, baseUrl);

    // For now, return a basic response
    // In a full implementation, would query the database directly
    return {
      actual: 0,
      expected: expectedCount,
      matches: false
    };
  } catch (error) {
    console.error(`Failed to verify player count for week ${weekId}:`, error);
    throw error;
  }
}

/**
 * Clear database before test (if backend supports it)
 * This is a placeholder - implement based on your API
 */
export async function clearDatabase(baseUrl: string = 'http://localhost:8000'): Promise<void> {
  try {
    // This would be a test-only endpoint
    await axios.post(`${baseUrl}/api/test/clear-database`);
  } catch (error) {
    console.warn('Could not clear database (endpoint may not exist):', error);
    // Don't throw - tests should still run
  }
}

/**
 * Seed database with test data (if backend supports it)
 * This is a placeholder - implement based on your API
 */
export async function seedTestData(baseUrl: string = 'http://localhost:8000'): Promise<void> {
  try {
    // This would be a test-only endpoint
    await axios.post(`${baseUrl}/api/test/seed-data`);
  } catch (error) {
    console.warn('Could not seed test data (endpoint may not exist):', error);
    // Don't throw - tests should still run
  }
}
