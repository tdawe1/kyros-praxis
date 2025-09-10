export class EventStore {
  append(stream, event) {
    console.log(`[eventstore] append to ${stream}:`, event)
  }
  read(stream) {
    console.log(`[eventstore] read from ${stream}`)
    return []
  }
}

