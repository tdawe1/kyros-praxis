/**
 * @jest-environment node
 */

import { 
  generateSecureSecret,
  generateApiKey,
  validateSecretStrength,
  SecureSecretStore,
  getEnvironmentSecret,
  generateNextAuthSecret,
} from '../secrets';

describe('Secret Management', () => {
  describe('generateSecureSecret', () => {
    test('should generate secret of specified length', () => {
      const secret = generateSecureSecret(32);
      
      // Base64URL encoded length is roughly 4/3 of original bytes
      expect(secret.length).toBeGreaterThan(40);
      expect(secret).toMatch(/^[A-Za-z0-9_-]+$/); // Base64URL pattern
    });

    test('should generate different secrets each time', () => {
      const secret1 = generateSecureSecret(32);
      const secret2 = generateSecureSecret(32);
      
      expect(secret1).not.toBe(secret2);
    });
  });

  describe('generateApiKey', () => {
    test('should generate API key with prefix', () => {
      const apiKey = generateApiKey('test', 32);
      
      expect(apiKey).toMatch(/^test_[A-Za-z0-9_-]+$/);
    });

    test('should use default prefix', () => {
      const apiKey = generateApiKey();
      
      expect(apiKey).toMatch(/^kyros_[A-Za-z0-9_-]+$/);
    });
  });

  describe('validateSecretStrength', () => {
    test('should validate strong secret positively', () => {
      const strongSecret = 'Th1s_1s_A_V3ry_Str0ng_S3cr3t_W1th_Sp3c14l_Ch4r5!@#$%';
      const result = validateSecretStrength(strongSecret);
      
      expect(result.valid).toBe(true);
      expect(result.score).toBeGreaterThanOrEqual(50);
      expect(result.issues).toHaveLength(0);
    });

    test('should reject weak secret', () => {
      const weakSecret = 'weak';
      const result = validateSecretStrength(weakSecret);
      
      expect(result.valid).toBe(false);
      expect(result.issues).toContain('Secret is too short (minimum 16 characters)');
    });

    test('should detect common patterns', () => {
      const commonSecret = 'password123';
      const result = validateSecretStrength(commonSecret);
      
      expect(result.valid).toBe(false);
      expect(result.issues.some(issue => issue.includes('common patterns'))).toBe(true);
    });

    test('should provide recommendations for medium strength secrets', () => {
      const mediumSecret = 'SomeRandomSecret123';
      const result = validateSecretStrength(mediumSecret);
      
      expect(result.recommendations.length).toBeGreaterThan(0);
    });
  });

  describe('SecureSecretStore', () => {
    let store: SecureSecretStore;

    beforeEach(() => {
      store = new SecureSecretStore(false); // Disable encryption for testing
    });

    test('should store and retrieve secrets', () => {
      const secretValue = 'test-secret-value';
      
      store.store('test-secret', secretValue, {
        name: 'Test Secret',
        type: 'password',
      });
      
      const retrieved = store.retrieve('test-secret');
      expect(retrieved).toBe(secretValue);
    });

    test('should return null for non-existent secret', () => {
      const retrieved = store.retrieve('non-existent');
      expect(retrieved).toBeNull();
    });

    test('should list secret metadata', () => {
      store.store('secret1', 'value1', {
        name: 'Secret 1',
        type: 'api_key',
      });
      
      store.store('secret2', 'value2', {
        name: 'Secret 2',
        type: 'oauth',
      });
      
      const metadata = store.list();
      expect(metadata).toHaveLength(2);
      expect(metadata[0].name).toBe('Secret 1');
      expect(metadata[1].name).toBe('Secret 2');
    });

    test('should track usage statistics', () => {
      store.store('tracked-secret', 'value', {
        name: 'Tracked Secret',
        type: 'password',
      });
      
      // Retrieve multiple times
      store.retrieve('tracked-secret');
      store.retrieve('tracked-secret');
      
      const metadata = store.list().find(m => m.id === 'tracked-secret');
      expect(metadata?.usage.usageCount).toBe(2);
      expect(metadata?.usage.lastUsed).toBeDefined();
    });

    test('should handle expired secrets', () => {
      const pastDate = new Date('2020-01-01');
      
      store.store('expired-secret', 'value', {
        name: 'Expired Secret',
        type: 'password',
        expiresAt: pastDate,
      });
      
      const retrieved = store.retrieve('expired-secret');
      expect(retrieved).toBeNull();
    });

    test('should identify secrets needing rotation', () => {
      const oldDate = new Date();
      oldDate.setDate(oldDate.getDate() - 100); // 100 days ago
      
      store.store('rotation-secret', 'value', {
        name: 'Rotation Secret',
        type: 'api_key',
        rotationSchedule: {
          enabled: true,
          intervalDays: 30,
          lastRotated: oldDate,
        },
      });
      
      const needingRotation = store.getSecretsNeedingRotation();
      expect(needingRotation).toHaveLength(1);
      expect(needingRotation[0].id).toBe('rotation-secret');
    });

    test('should remove secrets', () => {
      store.store('temp-secret', 'value', {
        name: 'Temporary Secret',
        type: 'password',
      });
      
      expect(store.retrieve('temp-secret')).toBe('value');
      
      const removed = store.remove('temp-secret');
      expect(removed).toBe(true);
      expect(store.retrieve('temp-secret')).toBeNull();
    });
  });

  describe('getEnvironmentSecret', () => {
    const originalEnv = process.env;

    beforeEach(() => {
      process.env = { ...originalEnv };
    });

    afterAll(() => {
      process.env = originalEnv;
    });

    test('should return environment variable value', () => {
      process.env.TEST_SECRET = 'test-value';
      
      const value = getEnvironmentSecret('TEST_SECRET');
      expect(value).toBe('test-value');
    });

    test('should return undefined for missing optional variable', () => {
      const value = getEnvironmentSecret('MISSING_SECRET', false);
      expect(value).toBeUndefined();
    });

    test('should throw error for missing required variable', () => {
      expect(() => {
        getEnvironmentSecret('MISSING_REQUIRED_SECRET', true);
      }).toThrow();
    });

    test('should warn about weak secrets', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      process.env.WEAK_SECRET = 'weak';
      
      getEnvironmentSecret('WEAK_SECRET');
      
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('generateNextAuthSecret', () => {
    test('should generate valid NextAuth secret', () => {
      const secret = generateNextAuthSecret();
      
      expect(secret).toBeDefined();
      expect(secret.length).toBeGreaterThan(50);
      
      const validation = validateSecretStrength(secret);
      expect(validation.valid).toBe(true);
    });
  });
});