/**
 * @jest-environment node
 */

import { NextRequest } from 'next/server';
import { withApiAuth, rateLimit } from '@/lib/api-auth';

// Mock NextAuth
jest.mock('@/lib/auth-v5', () => ({
  auth: jest.fn()
}));

// Mock jwt-decode
jest.mock('jwt-decode', () => ({
  jwtDecode: jest.fn()
}));

describe('Authentication Middleware', () => {
  describe('withApiAuth', () => {
    const mockHandler = jest.fn();
    const mockRequest = {
      headers: {
        get: jest.fn()
      },
      ip: '127.0.0.1'
    } as unknown as NextRequest;

    beforeEach(() => {
      jest.clearAllMocks();
      mockHandler.mockResolvedValue(new Response('Success', { status: 200 }));
    });

    it('should reject requests without authentication', async () => {
      const { jwtDecode } = require('jwt-decode');
      const { auth } = require('@/lib/auth-v5');
      
      (mockRequest.headers.get as jest.Mock).mockReturnValue(null);
      auth.mockResolvedValue(null);

      const protectedHandler = withApiAuth(mockHandler);
      const response = await protectedHandler(mockRequest);

      expect(response.status).toBe(401);
      const body = await response.json();
      expect(body.error).toBe('Authentication required');
    });

    it('should allow anonymous requests when configured', async () => {
      const { auth } = require('@/lib/auth-v5');
      
      (mockRequest.headers.get as jest.Mock).mockReturnValue(null);
      auth.mockResolvedValue(null);

      const protectedHandler = withApiAuth(mockHandler, { allowAnonymous: true });
      const response = await protectedHandler(mockRequest);

      expect(response.status).toBe(200);
      expect(mockHandler).toHaveBeenCalledWith(mockRequest);
    });

    it('should validate JWT tokens and add user to request', async () => {
      const { jwtDecode } = require('jwt-decode');
      
      const mockToken = 'valid.jwt.token';
      const mockDecoded = {
        sub: 'user123',
        email: 'test@example.com',
        name: 'Test User',
        exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
        roles: ['user']
      };

      (mockRequest.headers.get as jest.Mock).mockReturnValue(`Bearer ${mockToken}`);
      jwtDecode.mockReturnValue(mockDecoded);

      const protectedHandler = withApiAuth(mockHandler);
      await protectedHandler(mockRequest);

      expect(mockHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          user: {
            id: 'user123',
            email: 'test@example.com',
            name: 'Test User',
            roles: ['user']
          }
        })
      );
    });
  });

  describe('rateLimit', () => {
    it('should allow requests within limit', () => {
      const identifier = 'test-user-1';
      const limit = 5;
      const windowMs = 60000;

      for (let i = 0; i < limit; i++) {
        expect(rateLimit(identifier, limit, windowMs)).toBe(true);
      }
    });

    it('should reject requests exceeding limit', () => {
      const identifier = 'test-user-2';
      const limit = 3;
      const windowMs = 60000;

      // Use up the limit
      for (let i = 0; i < limit; i++) {
        expect(rateLimit(identifier, limit, windowMs)).toBe(true);
      }

      // Next request should be rejected
      expect(rateLimit(identifier, limit, windowMs)).toBe(false);
    });
  });
});