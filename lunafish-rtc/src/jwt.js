const crypto = require('crypto');

function base64UrlDecode(value) {
  const normalized = value
    .replace(/-/g, '+')
    .replace(/_/g, '/')
    .padEnd(Math.ceil(value.length / 4) * 4, '=');

  return Buffer.from(normalized, 'base64').toString('utf8');
}

function signHmacSha256(value, secret) {
  return crypto
    .createHmac('sha256', secret)
    .update(value)
    .digest('base64url');
}

function normalizePermissions(input = {}) {
  return {
    consume: Boolean(input.consume),
    produceAudio: Boolean(input.produceAudio),
    produceVideo: Boolean(input.produceVideo),
    produceScreen: false,
    manageRecording: false
  };
}

function verifyRtcToken(token, secret) {
  if (!token || typeof token !== 'string') {
    throw new Error('token is required');
  }

  const parts = token.split('.');

  if (parts.length !== 3) {
    throw new Error('invalid token format');
  }

  const [encodedHeader, encodedPayload, signature] = parts;
  const signingInput = `${encodedHeader}.${encodedPayload}`;
  const expectedSignature = signHmacSha256(signingInput, secret);
  const provided = Buffer.from(signature);
  const expected = Buffer.from(expectedSignature);

  if (
    provided.length !== expected.length ||
    !crypto.timingSafeEqual(provided, expected)
  ) {
    throw new Error('invalid token signature');
  }

  const header = JSON.parse(base64UrlDecode(encodedHeader));

  if (header.alg !== 'HS256') {
    throw new Error('unsupported token algorithm');
  }

  const claims = JSON.parse(base64UrlDecode(encodedPayload));
  const now = Math.floor(Date.now() / 1000);

  // Handle both old and new token formats
  // Old format: sub, room, permissions, exp, iat
  // New format: user_id, room_id, call_id, session_id, call_type, permissions, exp, iat
  
  // Map old fields to new fields for backward compatibility
  if (claims.sub && !claims.user_id) {
    claims.user_id = claims.sub;
  }
  
  if (claims.room && !claims.room_id) {
    claims.room_id = claims.room;
  }
  
  // For backward compatibility, generate missing fields
  if (!claims.call_id && claims.room_id) {
    claims.call_id = claims.room_id; // Use room_id as call_id for old tokens
  }
  
  if (!claims.session_id && claims.user_id && claims.room_id) {
    claims.session_id = `${claims.room_id}:${claims.user_id}`;
  }
  
  if (!claims.call_type) {
    claims.call_type = 'classroom';
  }

  // Now validate required fields
  if (!claims.call_id) throw new Error('token call_id is missing');
  if (!claims.room_id) throw new Error('token room_id is missing');
  if (!claims.user_id) throw new Error('token user_id is missing');
  if (!claims.session_id) throw new Error('token session_id is missing');
  if (!claims.call_type) throw new Error('token call_type is missing');
  if (!claims.exp || now >= claims.exp) throw new Error('token expired');

  claims.permissions = normalizePermissions(claims.permissions);

  return claims;
}

module.exports = {
  normalizePermissions,
  verifyRtcToken
};
