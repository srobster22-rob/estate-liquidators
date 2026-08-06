export interface SmsMessage { to: string; body: string; idempotencyKey: string }

export interface SmsProvider {
  readonly name: string;
  send(msg: SmsMessage): Promise<{ delivered: boolean; error?: string }>;
}

/** Selected automatically when no credentials are present, so the whole system demos with none. */
export class ConsoleSmsProvider implements SmsProvider {
  readonly name = 'console';
  readonly sent: SmsMessage[] = [];
  async send(msg: SmsMessage) {
    this.sent.push(msg);
    console.log(`  [sms → ${msg.to}] ${msg.body}`);
    return { delivered: true };
  }
}

/** Fails the first N attempts, to exercise retry and exactly-once delivery under failure. */
export class FlakySmsProvider implements SmsProvider {
  readonly name = 'flaky';
  readonly sent: SmsMessage[] = [];
  private attempts = 0;
  constructor(private readonly failFirst: number) {}
  async send(msg: SmsMessage) {
    this.attempts++;
    if (this.attempts <= this.failFirst) return { delivered: false, error: 'simulated failure' };
    this.sent.push(msg);
    return { delivered: true };
  }
}

export function pickProvider(env: Record<string, string | undefined>): SmsProvider {
  if (env.TWILIO_ACCOUNT_SID && env.TWILIO_AUTH_TOKEN) {
    throw new Error(
      'A real SMS provider is not implemented. Wire Twilio here, behind this same interface, ' +
        'and keep ConsoleSmsProvider working so the pipeline stays runnable without credentials.',
    );
  }
  return new ConsoleSmsProvider();
}
