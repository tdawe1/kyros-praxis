import { sanitizePathSegment, sanitizeAndJoinPaths, validateFilename } from '../pathSecurity';
import path from 'path';

describe('pathSecurity', () => {
  describe('sanitizePathSegment', () => {
    test('should remove .. sequences', () => {
      expect(sanitizePathSegment('valid../invalid')).toBe('valid/invalid');
      expect(sanitizePathSegment('../../../etc/passwd')).toBe('etc/passwd');
    });

    test('should remove null bytes', () => {
      expect(sanitizePathSegment('file\0name')).toBe('filename');
    });

    test('should remove invalid filename characters', () => {
      expect(sanitizePathSegment('file<name>:test|file?*')).toBe('filenametestfile');
    });

    test('should remove leading/trailing slashes', () => {
      expect(sanitizePathSegment('/valid/path/')).toBe('valid/path');
      expect(sanitizePathSegment('//multiple//slashes//')).toBe('multiple//slashes');
    });

    test('should prevent Windows absolute paths', () => {
      expect(sanitizePathSegment('C:/windows/system32')).toBe('windows/system32');
      expect(sanitizePathSegment('D:/data')).toBe('data');
    });

    test('should throw error for empty segments', () => {
      expect(() => sanitizePathSegment('')).toThrow('Invalid path segment: cannot be empty after sanitization');
      expect(() => sanitizePathSegment('   ')).toThrow('Invalid path segment: cannot be empty after sanitization');
      expect(() => sanitizePathSegment('../../../')).toThrow('Invalid path segment: cannot be empty after sanitization');
    });

    test('should throw error for non-string input', () => {
      expect(() => sanitizePathSegment(null as any)).toThrow('Path segment must be a string');
      expect(() => sanitizePathSegment(123 as any)).toThrow('Path segment must be a string');
    });

    test('should preserve valid segments', () => {
      expect(sanitizePathSegment('valid-file.txt')).toBe('valid-file.txt');
      expect(sanitizePathSegment('folder_name')).toBe('folder_name');
    });
  });

  describe('sanitizeAndJoinPaths', () => {
    const basePath = '/safe/base/path';

    test('should join sanitized paths correctly', () => {
      const result = sanitizeAndJoinPaths(basePath, 'subfolder', 'file.txt');
      expect(result).toBe(path.join(basePath, 'subfolder', 'file.txt'));
    });

    test('should prevent path traversal attacks', () => {
      expect(() => sanitizeAndJoinPaths(basePath, '../../evil')).toThrow('Path traversal attempt detected: .. sequences are not allowed');
      expect(() => sanitizeAndJoinPaths(basePath, 'valid', '../../../evil')).toThrow('Path traversal attempt detected: .. sequences are not allowed');
    });

    test('should sanitize each segment individually', () => {
      const result = sanitizeAndJoinPaths(basePath, 'sub<folder>', 'file:name.txt');
      expect(result).toBe(path.join(basePath, 'subfolder', 'filename.txt'));
    });

    test('should throw error for non-string base path', () => {
      expect(() => sanitizeAndJoinPaths(null as any, 'test')).toThrow('Base path must be a string');
    });

    test('should handle empty segments array', () => {
      const result = sanitizeAndJoinPaths(basePath);
      expect(result).toBe(basePath);
    });
  });

  describe('validateFilename', () => {
    test('should accept valid filenames', () => {
      expect(validateFilename('valid-file.txt')).toBe('valid-file.txt');
      expect(validateFilename('document_2023.pdf')).toBe('document_2023.pdf');
      expect(validateFilename('image.jpg')).toBe('image.jpg');
    });

    test('should reject filenames with path traversal patterns', () => {
      expect(() => validateFilename('../file.txt')).toThrow('Filename cannot contain path traversal patterns');
      expect(() => validateFilename('../../etc/passwd')).toThrow('Filename cannot contain path traversal patterns');
      expect(() => validateFilename('folder/file.txt')).toThrow('Filename cannot contain path traversal patterns');
      expect(() => validateFilename('folder\\file.txt')).toThrow('Filename cannot contain path traversal patterns');
    });

    test('should remove null bytes', () => {
      expect(validateFilename('file\0name.txt')).toBe('filename.txt');
    });

    test('should reject invalid characters', () => {
      expect(() => validateFilename('file<name>.txt')).toThrow('Filename contains invalid characters');
      expect(() => validateFilename('file:name.txt')).toThrow('Filename contains invalid characters');
      expect(() => validateFilename('file|name.txt')).toThrow('Filename contains invalid characters');
      expect(() => validateFilename('file?name.txt')).toThrow('Filename contains invalid characters');
      expect(() => validateFilename('file*name.txt')).toThrow('Filename contains invalid characters');
    });

    test('should reject empty filenames', () => {
      expect(() => validateFilename('')).toThrow('Filename cannot be empty');
      expect(() => validateFilename('   ')).toThrow('Filename cannot be empty');
    });

    test('should throw error for non-string input', () => {
      expect(() => validateFilename(null as any)).toThrow('Filename must be a string');
      expect(() => validateFilename(123 as any)).toThrow('Filename must be a string');
    });
  });
});