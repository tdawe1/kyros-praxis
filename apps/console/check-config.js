// Quick script to check what API_BASE will be at runtime
console.log('Environment check:');
console.log('NEXT_PUBLIC_API_BASE_URL:', process.env.NEXT_PUBLIC_API_BASE_URL);
console.log('');

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8001';
console.log('Computed API_BASE:', API_BASE);
console.log('');
console.log('Expected: /api');
console.log('Match:', API_BASE === '/api' ? '✅ CORRECT' : '❌ WRONG');
