import { setupServer } from 'msw';
import { handlers } from './handlers';

const server = setupServer(...handlers);

export { server };