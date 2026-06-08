const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('crypto');

const { buildSignature } = require('../src/callbacks');
const { normalizePermissions, verifyRtcToken } = require('../src/jwt');

function createToken(payload, secret) {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString(
    'base64url'
  );
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const signature = crypto
    .createHmac('sha256', secret)
    .update(`${header}.${body}`)
    .digest('base64url');

  return `${header}.${body}.${signature}`;
}

test('verifyRtcToken accepts a valid token', () => {
  const token = createToken(
    {
      call_id: 'call-1',
      room_id: 'room-1',
      user_id: '7',
      session_id: 'session-1',
      call_type: 'audio',
      permissions: {
        consume: true,
        produceAudio: true
      },
      exp: Math.floor(Date.now() / 1000) + 60
    },
    'secret'
  );
  const claims = verifyRtcToken(token, 'secret');

  assert.equal(claims.call_id, 'call-1');
  assert.deepEqual(claims.permissions, {
    consume: true,
    produceAudio: true,
    produceVideo: false,
    produceScreen: false,
    manageRecording: false
  });
});

test('verifyRtcToken rejects expired tokens', () => {
  const token = createToken(
    {
      call_id: 'call-1',
      room_id: 'room-1',
      user_id: '7',
      session_id: 'session-1',
      call_type: 'audio',
      permissions: {
        consume: true
      },
      exp: Math.floor(Date.now() / 1000) - 1
    },
    'secret'
  );

  assert.throws(() => verifyRtcToken(token, 'secret'), /token expired/);
});

test('verifyRtcToken rejects invalid signatures', () => {
  const token = createToken(
    {
      call_id: 'call-1',
      room_id: 'room-1',
      user_id: '7',
      session_id: 'session-1',
      call_type: 'audio',
      permissions: {
        consume: true
      },
      exp: Math.floor(Date.now() / 1000) + 60
    },
    'secret'
  );

  assert.throws(() => verifyRtcToken(token, 'wrong-secret'), /invalid token signature/);
});

test('normalizePermissions removes unsupported features', () => {
  assert.deepEqual(
    normalizePermissions({
      consume: true,
      produceAudio: true,
      produceVideo: true,
      produceScreen: true,
      manageRecording: true
    }),
    {
      consume: true,
      produceAudio: true,
      produceVideo: true,
      produceScreen: false,
      manageRecording: false
    }
  );
});

test('buildSignature signs callback payloads deterministically', () => {
  const signature = buildSignature({
    timestamp: '123',
    rawBody: '{"event":"participant_joined"}',
    secret: 'internal'
  });

  assert.equal(signature.length, 64);
  assert.equal(
    signature,
    buildSignature({
      timestamp: '123',
      rawBody: '{"event":"participant_joined"}',
      secret: 'internal'
    })
  );
});
