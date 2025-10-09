/**
 * Security tests for repoRoot module
 * Verifies that path traversal vulnerabilities are prevented
 * and existing functionality still works correctly
 */

import { repoFile, resolveRepoRoot, devlogsDir } from '../app/lib/server/repoRoot';
import path from 'path';
import fs from 'fs';

// Mock fs for testing
jest.mock('fs');
const mockFs = fs as jest.Mocked<typeof fs>;

describe('repoRoot Security', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock process.cwd() to return a consistent test directory
    jest.spyOn(process, 'cwd').mockReturnValue('/test/root');
    
    // Mock fs.existsSync to return false for most paths, true for our test root
    mockFs.existsSync.mockImplementation((path: any) => {
      const pathStr = path.toString();
      return pathStr.includes('.git') || pathStr.includes('afkimplement1.md');
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('repoFile function security', () => {
    it('should allow normal file paths', () => {
      const result = repoFile('docs', 'plan.md');
      expect(result).toContain('docs');
      expect(result).toContain('plan.md');
    });

    it('should allow nested directory paths', () => {
      const result = repoFile('services', 'console', 'app', 'page.tsx');
      expect(result).toContain(path.join('services', 'console', 'app', 'page.tsx'));
    });

    it('should reject path traversal with double dots', () => {
      expect(() => {
        repoFile('..', 'etc', 'passwd');
      }).toThrow('Invalid path segment: ..');
    });

    it('should reject path traversal in subdirectories', () => {
      expect(() => {
        repoFile('docs', '..', '..', 'etc', 'passwd');
      }).toThrow('Invalid path segment: ..');
    });

    it('should reject relative path notation', () => {
      expect(() => {
        repoFile('./config', '../secrets');
      }).toThrow('Invalid path segment: ./config');
    });

    it('should reject Windows-style relative paths', () => {
      expect(() => {
        repoFile('config', '..\\secrets');
      }).toThrow('Invalid path segment: ..\\secrets');
    });

    it('should reject absolute paths', () => {
      expect(() => {
        repoFile('/etc/passwd');
      }).toThrow('Absolute paths not allowed: /etc/passwd');
    });

    it('should reject Windows absolute paths', () => {
      expect(() => {
        repoFile('C:\\Windows\\System32');
      }).toThrow('Absolute paths not allowed: C:\\Windows\\System32');
    });

    it('should filter out empty segments', () => {
      const result = repoFile('docs', '', 'plan.md', '   ', 'readme.txt');
      expect(result).toContain('docs');
      expect(result).toContain('plan.md');
      expect(result).toContain('readme.txt');
      // Should not contain empty segments
      expect(result).not.toMatch(/\/\/+/);
    });

    it('should handle single valid segment', () => {
      const result = repoFile('README.md');
      expect(result).toContain('README.md');
    });

    it('should ensure path stays within repository root', () => {
      // This test verifies that even if somehow a traversal gets through,
      // the final check ensures we stay within bounds
      const result = repoFile('docs', 'plan.md');
      const resolvedRoot = path.resolve('/test/root');
      expect(result.startsWith(resolvedRoot)).toBe(true);
    });

    it('should reject complex traversal attempts', () => {
      expect(() => {
        repoFile('docs', '..', 'sensitive');
      }).toThrow('Invalid path segment: ..');
    });

    it('should reject encoded traversal attempts', () => {
      // Test URL-encoded double dots
      expect(() => {
        repoFile('docs', '%2e%2e', 'sensitive');
      }).toThrow('Invalid path segment: %2e%2e');
    });
  });

  describe('devlogsDir function', () => {
    it('should create devlogs directory safely', () => {
      mockFs.existsSync.mockReturnValue(false);
      mockFs.mkdirSync.mockImplementation(() => {});
      
      const result = devlogsDir();
      expect(result).toContain('.devlogs');
      expect(mockFs.mkdirSync).toHaveBeenCalledWith(expect.stringContaining('.devlogs'), { recursive: true });
    });

    it('should return existing devlogs directory', () => {
      mockFs.existsSync.mockReturnValue(true);
      
      const result = devlogsDir();
      expect(result).toContain('.devlogs');
      expect(mockFs.mkdirSync).not.toHaveBeenCalled();
    });
  });

  describe('resolveRepoRoot function', () => {
    it('should find repository root with .git directory', () => {
      mockFs.existsSync.mockImplementation((path: any) => {
        return path.toString().endsWith('.git');
      });
      
      const result = resolveRepoRoot();
      expect(result).toBeDefined();
    });

    it('should find repository root with marker file', () => {
      mockFs.existsSync.mockImplementation((path: any) => {
        return path.toString().endsWith('afkimplement1.md');
      });
      
      const result = resolveRepoRoot();
      expect(result).toBeDefined();
    });

    it('should fallback to current directory when no markers found', () => {
      mockFs.existsSync.mockReturnValue(false);
      
      const result = resolveRepoRoot();
      expect(result).toBe('/test/root');
    });

    it('should use provided start directory', () => {
      const customStart = '/custom/start';
      mockFs.existsSync.mockReturnValue(false);
      
      const result = resolveRepoRoot(customStart);
      expect(result).toBe(customStart);
    });
  });

  describe('Integration with existing usage', () => {
    it('should work with review-plan usage pattern', () => {
      // Test the pattern used in review-plan/page.tsx
      const result = repoFile('docs', 'review-plan.md');
      expect(result).toContain(path.join('docs', 'review-plan.md'));
    });

    it('should work with devlogs usage pattern', () => {
      // Test the pattern used in devlogs.ts
      mockFs.existsSync.mockReturnValue(false);
      mockFs.mkdirSync.mockImplementation(() => {});
      
      const logsDir = devlogsDir();
      const filePath = path.join(logsDir, 'super-audit.json');
      expect(filePath).toContain('.devlogs');
      expect(filePath).toContain('super-audit.json');
    });
  });
});