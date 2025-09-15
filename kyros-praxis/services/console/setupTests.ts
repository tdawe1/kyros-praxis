  import '@testing-library/jest-dom'

// Add missing Node.js globals for MSW
import { TextEncoder, TextDecoder } from 'util';
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Polyfill fetch and related APIs for MSW
import 'whatwg-fetch';

// Polyfill BroadcastChannel for MSW WebSocket support
global.BroadcastChannel = class BroadcastChannel {
  constructor(name: string) {
    this.name = name;
  }
  name: string;
  postMessage() {}
  close() {}
  onmessage = null;
  onmessageerror = null;
} as any;

// Add fetch for tests
global.fetch = jest.fn();

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
}));