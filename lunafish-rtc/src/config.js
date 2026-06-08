function parseInteger(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function parseList(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function requireValue(name, value) {
  if (!value) {
    throw new Error(`missing required environment variable: ${name}`);
  }

  return value;
}

function loadConfig(env) {
  return {
    host: env.HOST || '127.0.0.1',
    port: parseInteger(env.PORT, 3001),
    wsPath: env.RTC_WS_PATH || '/rtc/ws',
    publicIp: env.PUBLIC_IP || '127.0.0.1',
    rtcJwtSecret: requireValue('RTC_JWT_SECRET', env.RTC_JWT_SECRET),
    rtcStunUrls: parseList(env.RTC_STUN_URLS),
    rtcTurnUrls: parseList(env.RTC_TURN_URLS),
    rtcTurnUsername: env.RTC_TURN_USERNAME || '',
    rtcTurnCredential: env.RTC_TURN_CREDENTIAL || '',
    iceTransportPolicy:
      env.RTC_ICE_TRANSPORT_POLICY === 'relay' ? 'relay' : 'all',
    mediasoupLogLevel: env.MEDIASOUP_LOG_LEVEL || 'warn',
    rtcMinPort: parseInteger(env.RTC_MIN_PORT, 40000),
    rtcMaxPort: parseInteger(env.RTC_MAX_PORT, 40100),
    djangoInternalCallbackUrl: env.DJANGO_INTERNAL_CALLBACK_URL || '',
    internalCallbackSecret: env.INTERNAL_CALLBACK_SECRET || '',
    internalCallbackTimeoutMs: parseInteger(
      env.INTERNAL_CALLBACK_TIMEOUT_MS,
      5000
    )
  };
}

module.exports = {
  loadConfig
};
