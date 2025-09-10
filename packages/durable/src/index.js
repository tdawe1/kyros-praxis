export class DurableTask {
  constructor(id) { this.id = id }
  checkpoint(state) { console.log('[durable] checkpoint', this.id, state) }
}

