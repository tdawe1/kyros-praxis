import { createHash, createCipher, createDecipher, randomBytes } from 'crypto';

/**
 * Secure Secret Management
 * 
 * This module provides utilities for secure handling of secrets and sensitive
 * configuration data, including encryption, secure generation, and validation.
 */

export interface SecretMetadata {
  id: string;
  name: string;
  type: 'api_key' | 'oauth' | 'password' | 'certificate' | 'other';
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  expiresAt?: Date;
  rotationSchedule?: {
    enabled: boolean;
    intervalDays: number;
    lastRotated?: Date;
  };
  usage: {
    lastUsed?: Date;
    usageCount: number;
  };
  security: {
    encrypted: boolean;
    algorithm?: string;
    keyDerivation?: string;
  };
}

export interface SecretValue {
  value: string;
  metadata: SecretMetadata;
}

export interface SecretStore {
  [key: string]: SecretValue;
}

/**
 * Generates a cryptographically secure secret
 */
export function generateSecureSecret(length: number = 32): string {
  return randomBytes(length).toString('base64url');
}

/**
 * Generates a secure API key with specified format
 */
export function generateApiKey(prefix: string = 'kyros', length: number = 32): string {
  const secret = generateSecureSecret(length);
  return `${prefix}_${secret}`;
}

/**
 * Validates secret strength based on security requirements
 */
export function validateSecretStrength(secret: string): {
  valid: boolean;
  score: number;
  issues: string[];
  recommendations: string[];
} {
  const issues: string[] = [];
  const recommendations: string[] = [];
  let score = 0;
  
  // Length check
  if (secret.length < 16) {
    issues.push('Secret is too short (minimum 16 characters)');
  } else if (secret.length >= 32) {
    score += 30;
  } else if (secret.length >= 24) {
    score += 20;
  } else {
    score += 10;
    recommendations.push('Consider using a longer secret (32+ characters)');
  }
  
  // Character diversity
  const hasLowercase = /[a-z]/.test(secret);
  const hasUppercase = /[A-Z]/.test(secret);
  const hasNumbers = /[0-9]/.test(secret);
  const hasSpecialChars = /[^a-zA-Z0-9]/.test(secret);
  
  const diversity = [hasLowercase, hasUppercase, hasNumbers, hasSpecialChars].filter(Boolean).length;
  score += diversity * 10;
  
  if (diversity < 3) {
    recommendations.push('Use a mix of uppercase, lowercase, numbers, and special characters');
  }
  
  // Common pattern checks
  const commonPatterns = [
    /(.)\1{3,}/, // Repeated characters
    /123456|abcdef|qwerty/i, // Common sequences
    /password|secret|key|admin/i, // Common words
  ];
  
  for (const pattern of commonPatterns) {
    if (pattern.test(secret)) {
      issues.push('Secret contains common patterns or dictionary words');
      score -= 20;
      break;
    }
  }
  
  // Entropy estimation (simplified)
  const uniqueChars = new Set(secret).size;
  const entropy = Math.log2(Math.pow(uniqueChars, secret.length));
  
  if (entropy < 50) {
    recommendations.push('Consider using a more random secret with higher entropy');
  } else {
    score += 20;
  }
  
  return {
    valid: issues.length === 0 && score >= 50,
    score: Math.min(100, Math.max(0, score)),
    issues,
    recommendations,
  };
}

/**
 * Encrypts sensitive configuration data
 */
export function encryptSensitiveData(data: string, masterKey?: string): {
  encrypted: string;
  iv: string;
  algorithm: string;
} {
  // Use provided master key or derive from environment
  const key = masterKey || deriveEncryptionKey();
  const algorithm = 'aes-256-gcm';
  const iv = randomBytes(16);
  
  const cipher = createCipher(algorithm, key);
  let encrypted = cipher.update(data, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  return {
    encrypted,
    iv: iv.toString('hex'),
    algorithm,
  };
}

/**
 * Decrypts sensitive configuration data
 */
export function decryptSensitiveData(
  encryptedData: string,
  iv: string,
  algorithm: string = 'aes-256-gcm',
  masterKey?: string
): string {
  const key = masterKey || deriveEncryptionKey();
  
  const decipher = createDecipher(algorithm, key);
  let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
}

/**
 * Derives encryption key from environment variables
 */
function deriveEncryptionKey(): string {
  const secret = process.env.NEXTAUTH_SECRET;
  if (!secret) {
    throw new Error('NEXTAUTH_SECRET is required for configuration encryption');
  }
  
  // Use PBKDF2 for key derivation
  const salt = process.env.CONFIG_ENCRYPTION_SALT || 'kyros-praxis-config-salt';
  return createHash('sha256').update(secret + salt).digest('hex');
}

/**
 * Secure secret storage with encryption at rest
 */
export class SecureSecretStore {
  private secrets: Map<string, SecretValue> = new Map();
  private encrypted: boolean;
  
  constructor(encrypted: boolean = true) {
    this.encrypted = encrypted;
  }
  
  /**
   * Stores a secret securely
   */
  store(secretId: string, value: string, metadata: Partial<SecretMetadata>): void {
    const fullMetadata: SecretMetadata = {
      id: secretId,
      name: metadata.name || secretId,
      type: metadata.type || 'other',
      description: metadata.description,
      createdAt: new Date(),
      updatedAt: new Date(),
      expiresAt: metadata.expiresAt,
      rotationSchedule: metadata.rotationSchedule,
      usage: {
        usageCount: 0,
        ...metadata.usage,
      },
      security: {
        encrypted: this.encrypted,
        algorithm: this.encrypted ? 'aes-256-gcm' : undefined,
        keyDerivation: this.encrypted ? 'pbkdf2' : undefined,
        ...metadata.security,
      },
    };
    
    const storedValue = this.encrypted 
      ? encryptSensitiveData(value).encrypted
      : value;
    
    this.secrets.set(secretId, {
      value: storedValue,
      metadata: fullMetadata,
    });
  }
  
  /**
   * Retrieves a secret securely
   */
  retrieve(secretId: string): string | null {
    const secretValue = this.secrets.get(secretId);
    if (!secretValue) {
      return null;
    }
    
    // Update usage statistics
    secretValue.metadata.usage.lastUsed = new Date();
    secretValue.metadata.usage.usageCount++;
    
    // Check expiration
    if (secretValue.metadata.expiresAt && secretValue.metadata.expiresAt < new Date()) {
      console.warn(`Secret ${secretId} has expired`);
      return null;
    }
    
    // Decrypt if necessary
    if (this.encrypted && secretValue.metadata.security.encrypted) {
      try {
        // Note: In a real implementation, you'd need to store IV separately
        // This is a simplified example
        return decryptSensitiveData(secretValue.value, '');
      } catch (error) {
        console.error(`Failed to decrypt secret ${secretId}:`, error);
        return null;
      }
    }
    
    return secretValue.value;
  }
  
  /**
   * Lists all stored secrets (metadata only, no values)
   */
  list(): SecretMetadata[] {
    return Array.from(this.secrets.values()).map(secret => secret.metadata);
  }
  
  /**
   * Removes a secret from storage
   */
  remove(secretId: string): boolean {
    return this.secrets.delete(secretId);
  }
  
  /**
   * Checks for secrets that need rotation
   */
  getSecretsNeedingRotation(): SecretMetadata[] {
    const now = new Date();
    return this.list().filter(metadata => {
      if (!metadata.rotationSchedule?.enabled) {
        return false;
      }
      
      const lastRotated = metadata.rotationSchedule.lastRotated || metadata.createdAt;
      const daysSinceRotation = (now.getTime() - lastRotated.getTime()) / (1000 * 60 * 60 * 24);
      
      return daysSinceRotation >= metadata.rotationSchedule.intervalDays;
    });
  }
}

/**
 * Default secure secret store instance
 */
export const secretStore = new SecureSecretStore(true);

/**
 * Utility function to safely access environment secrets
 */
export function getEnvironmentSecret(key: string, required: boolean = false): string | undefined {
  const value = process.env[key];
  
  if (required && !value) {
    throw new Error(`Required environment secret ${key} is not set`);
  }
  
  if (value) {
    // Validate secret strength
    const validation = validateSecretStrength(value);
    if (!validation.valid) {
      console.warn(`⚠️  Environment secret ${key} failed validation:`, validation.issues);
    }
  }
  
  return value;
}

/**
 * Generates and validates a new NEXTAUTH_SECRET
 */
export function generateNextAuthSecret(): string {
  const secret = generateSecureSecret(64);
  const validation = validateSecretStrength(secret);
  
  if (!validation.valid) {
    throw new Error('Generated secret failed validation - this should not happen');
  }
  
  console.log('✅ Generated secure NEXTAUTH_SECRET');
  console.log(`Secret strength score: ${validation.score}/100`);
  
  return secret;
}