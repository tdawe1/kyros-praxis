import 'reflect-metadata';
import { Container } from 'inversify';
export type { Job, CoordinateEvent, AuthToken, ServiceHealth, Injectable } from './types';
export type { JobSchema, CoordinateEventSchema, AuthTokenSchema, ServiceHealthSchema } from './validation';
export { validate } from './validation';

// DI Container
export const container = new Container();

// DI Helpers
export function injectable(): ClassDecorator {
  return (target) => {
    // Decorator for injectable classes (Inversify handles binding)
  };
}

// Example DI binding
container.bind<Container>('Container').toConstantValue(container);