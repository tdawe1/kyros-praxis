// Mock server for testing - simplified for Jest setup
let handlers = [];

export const server = {
  listen: () => {},
  resetHandlers: () => { handlers = []; },
  close: () => {},
  use: (...newHandlers) => { handlers.push(...newHandlers); },
};