require('dotenv').config();
const { loadConfig } = require('./src/config');
const { createRtcServer } = require('./src/rtcServer');

async function main() {
  const config = loadConfig(process.env);
  const server = await createRtcServer(config);

  server.listen(config.port, config.host, () => {
    console.log('rtc server listening', {
      host: config.host,
      port: config.port,
      wsPath: config.wsPath,
      publicIp: config.publicIp
    });
  });
}

main().catch((error) => {
  console.error('failed to start rtc server', error);
  process.exit(1);
});
