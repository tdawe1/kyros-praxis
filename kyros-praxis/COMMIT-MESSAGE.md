feat: Implement P0/P1 security fixes for Kyros Praxis

This commit addresses all P0-CRITICAL and P1-HIGH security vulnerabilities identified in the security audit:

## P0-CRITICAL Fixes:
- Remove committed .env files containing sensitive credentials
- Fix JWT implementation to include proper claims and error handling
- Replace NextAuth dev-only authorize with real verification

## P1-HIGH Fixes:
- Apply security middleware in orchestrator service
- Fix WebSocket authentication by passing JWT tokens as query parameters
- Update CSRF protection to exempt API endpoints that use JWT authentication

## Additional Improvements:
- Create .env.example files for proper secrets management
- Add pre-commit hook to prevent committing secrets
- Centralize JWT configuration in app/core/config.py
- Use HS512 algorithm instead of HS256 for stronger security
- Fix NextAuth to authenticate against orchestrator API
- Add HTTPS support in production environments
- Update tests to ensure all security fixes are working

## Test Results:
- Authentication tests: 4/4 passed
- Security tests: 15/15 passed

These changes significantly improve the security posture of the Kyros Praxis codebase by addressing the most critical vulnerabilities and establishing a solid foundation for secure authentication and authorization.