export function project(events, reducer, initial) {
  return events.reduce(reducer, initial)
}

