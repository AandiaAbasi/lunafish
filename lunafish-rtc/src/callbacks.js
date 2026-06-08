const crypto = require('crypto');

function buildSignature({ timestamp, rawBody, secret }) {
  return crypto
    .createHmac('sha256', secret)
    .update(`${timestamp}.${rawBody}`)
    .digest('hex');
}

async function postPresenceEvent(config, event, peer) {
  if (!config.djangoInternalCallbackUrl) {
    return { skipped: true, reason: 'missing-url' };
  }

  if (!config.internalCallbackSecret) {
    throw new Error('INTERNAL_CALLBACK_SECRET is required for presence callbacks');
  }

  const payload = {
    event,
    call_id: peer.callId,
    room_id: peer.roomId,
    user_id: peer.userId,
    session_id: peer.sessionId,
    peer_id: peer.id,
    call_type: peer.callType,
    occurred_at: new Date().toISOString()
  };
  const rawBody = JSON.stringify(payload);
  const timestamp = String(Math.floor(Date.now() / 1000));
  const signature = buildSignature({
    timestamp,
    rawBody,
    secret: config.internalCallbackSecret
  });
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), config.internalCallbackTimeoutMs);

  try {
    const response = await fetch(config.djangoInternalCallbackUrl, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-internal-timestamp': timestamp,
        'x-internal-signature': signature
      },
      body: rawBody,
      signal: controller.signal
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`presence callback failed (${response.status}): ${body}`);
    }

    return { ok: true };
  } finally {
    clearTimeout(timeout);
  }
}

module.exports = {
  buildSignature,
  postPresenceEvent
};
