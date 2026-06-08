const http = require('http');
const express = require('express');
const mediasoup = require('mediasoup');
const { WebSocketServer } = require('ws');

const { postPresenceEvent } = require('./callbacks');
const { normalizePermissions, verifyRtcToken } = require('./jwt');

function getIceConfiguration(config) {
  const iceServers = [];

  if (config.rtcStunUrls.length > 0) {
    iceServers.push({ urls: config.rtcStunUrls });
  }

  if (config.rtcTurnUrls.length > 0) {
    iceServers.push({
      urls: config.rtcTurnUrls,
      username: config.rtcTurnUsername,
      credential: config.rtcTurnCredential
    });
  }

  return {
    iceServers,
    iceTransportPolicy: config.iceTransportPolicy
  };
}

function serializeTransportState(peer, direction) {
  const transport = direction === 'send' ? peer.sendTransport : peer.recvTransport;
  const state = peer.transportState?.[direction] || {};

  if (!transport && !state.id) {
    return null;
  }

  return {
    id: transport?.id || state.id || null,
    iceState: state.iceState || transport?.iceState || null,
    dtlsState: state.dtlsState || transport?.dtlsState || null
  };
}

function serializePeer(peer) {
  return {
    peerId: peer.id,
    userId: peer.userId,
    sessionId: peer.sessionId,
    roomId: peer.roomId,
    callId: peer.callId,
    callType: peer.callType,
    permissions: peer.permissions
  };
}

function serializePeerObservability(peer) {
  return {
    ...serializePeer(peer),
    joinedAt: peer.joinedAt || null,
    transportState: {
      send: serializeTransportState(peer, 'send'),
      recv: serializeTransportState(peer, 'recv')
    },
    producerCount: peer.producers.size,
    consumerCount: peer.consumers.size,
    producers: [...peer.producers.keys()],
    consumers: [...peer.consumers.keys()]
  };
}

function serializeProducerInfo(producerId, info) {
  return {
    producerId,
    peerId: info.peerId,
    userId: info.userId,
    roomId: info.roomId,
    callId: info.callId,
    kind: info.kind,
    source: info.source
  };
}

function ensureJoinedRoom(peer) {
  if (!peer.roomId) {
    throw new Error('join a room first');
  }
}

function ensureCanConsume(peer) {
  if (!peer.permissions.consume) {
    throw new Error('consume is not allowed for this session');
  }
}

function ensureCanSend(peer) {
  if (!peer.permissions.produceAudio && !peer.permissions.produceVideo) {
    throw new Error('sending media is not allowed for this session');
  }
}

function ensureCanProduce(peer, kind, source) {
  if (source === 'screen') {
    throw new Error('screen sharing is not enabled in this service');
  }

  if (kind === 'audio' && !peer.permissions.produceAudio) {
    throw new Error('audio publishing is not allowed for this session');
  }

  if (kind === 'video' && !peer.permissions.produceVideo) {
    throw new Error('video publishing is not allowed for this session');
  }
}

function getPreferredLayersForProfile(profile) {
  if (profile === 'low') {
    return { spatialLayer: 0, temporalLayer: 0 };
  }

  if (profile === 'medium') {
    return { spatialLayer: 1, temporalLayer: 1 };
  }

  if (profile === 'high') {
    return { spatialLayer: 2, temporalLayer: 2 };
  }

  throw new Error(`invalid consumer profile: ${profile}`);
}

async function applyConsumerProfile(consumer, profile) {
  if (consumer.kind !== 'video') {
    return { applied: false, reason: 'not-video' };
  }

  if (typeof consumer.setPreferredLayers !== 'function') {
    return { applied: false, reason: 'no-layer-control' };
  }

  if (consumer.type !== 'simulcast' && consumer.type !== 'svc') {
    return { applied: false, reason: `unsupported-consumer-type:${consumer.type}` };
  }

  const layers = getPreferredLayersForProfile(profile);
  await consumer.setPreferredLayers(layers);

  return {
    applied: true,
    profile,
    layers
  };
}

async function createRtcServer(config) {
  const app = express();
  const server = http.createServer(app);
  const wss = new WebSocketServer({ noServer: true });
  const peers = new Map();
  const rooms = new Map();
  const producers = new Map();
  const counters = {
    wsConnectionsOpened: 0,
    wsConnectionsClosed: 0,
    roomJoins: 0,
    produces: 0,
    consumes: 0,
    errors: 0
  };
  let nextPeerNumber = 1;
  const startedAt = new Date().toISOString();

  process.on('uncaughtException', (error) => {
    console.error('uncaughtException', error);
  });

  process.on('unhandledRejection', (error) => {
    console.error('unhandledRejection', error);
  });

  const worker = await mediasoup.createWorker({
    logLevel: config.mediasoupLogLevel,
    rtcMinPort: config.rtcMinPort,
    rtcMaxPort: config.rtcMaxPort
  });

  worker.on('died', () => {
    console.error('mediasoup worker died');
    process.exit(1);
  });

  const router = await worker.createRouter({
    mediaCodecs: [
      {
        kind: 'audio',
        mimeType: 'audio/opus',
        clockRate: 48000,
        channels: 2
      },
      {
        kind: 'video',
        mimeType: 'video/VP8',
        clockRate: 90000
      }
    ]
  });

  function send(ws, payload) {
    ws.send(JSON.stringify(payload));
  }

  function getPeer(ws) {
    const peer = peers.get(ws);

    if (!peer) {
      throw new Error('peer not found');
    }

    return peer;
  }

  function getTransport(peer, direction) {
    if (direction === 'send') return peer.sendTransport;
    if (direction === 'recv') return peer.recvTransport;
    throw new Error(`invalid direction: ${direction}`);
  }

  function serializeTransport(transport) {
    const iceConfiguration = getIceConfiguration(config);

    return {
      id: transport.id,
      iceParameters: transport.iceParameters,
      iceCandidates: transport.iceCandidates,
      dtlsParameters: transport.dtlsParameters,
      iceServers: iceConfiguration.iceServers,
      iceTransportPolicy: iceConfiguration.iceTransportPolicy
    };
  }

  async function createWebRtcTransport() {
    return router.createWebRtcTransport({
      listenInfos: [
        {
          protocol: 'udp',
          ip: '0.0.0.0',
          announcedAddress: config.publicIp
        },
        {
          protocol: 'tcp',
          ip: '0.0.0.0',
          announcedAddress: config.publicIp
        }
      ]
    });
  }

  function getOrCreateRoom(roomId) {
    let room = rooms.get(roomId);

    if (!room) {
      room = {
        id: roomId,
        peerIds: new Set()
      };
      rooms.set(roomId, room);
    }

    return room;
  }

  function getRoomPeerSnapshots(roomId, excludePeerId = null) {
    const snapshots = [];

    for (const peer of peers.values()) {
      if (peer.roomId !== roomId) continue;
      if (excludePeerId && peer.id === excludePeerId) continue;
      snapshots.push(serializePeer(peer));
    }

    return snapshots;
  }

  function broadcastToRoom(roomId, exceptWs, payload) {
    for (const [ws, peer] of peers.entries()) {
      if (ws === exceptWs) continue;
      if (peer.roomId !== roomId) continue;
      send(ws, payload);
    }
  }

  function removePeerFromRoom(peer) {
    if (!peer.roomId) {
      return;
    }

    const room = rooms.get(peer.roomId);

    if (room) {
      room.peerIds.delete(peer.id);

      if (room.peerIds.size === 0) {
        rooms.delete(peer.roomId);
      }
    }
  }

  function closePeerMedia(peer, ws) {
    const roomId = peer.roomId;
    const closedProducerEntries = [];

    for (const [producerId, producer] of peer.producers.entries()) {
      const info = producers.get(producerId);

      if (info) {
        closedProducerEntries.push([producerId, info]);
        producers.delete(producerId);
      }

      peer.producers.delete(producerId);
      producer.close();
    }

    for (const consumer of peer.consumers.values()) {
      consumer.close();
    }

    if (peer.sendTransport) {
      peer.sendTransport.close();
    }

    if (peer.recvTransport) {
      peer.recvTransport.close();
    }

    peer.producers.clear();
    peer.consumers.clear();
    peer.sendTransport = null;
    peer.recvTransport = null;
    peer.transportState = {
      send: null,
      recv: null
    };

    if (roomId) {
      for (const [producerId, info] of closedProducerEntries) {
        broadcastToRoom(roomId, ws, {
          event: 'producerClosed',
          data: serializeProducerInfo(producerId, info)
        });
      }
    }
  }

  async function leaveCurrentRoom(peer, ws, eventName) {
    if (!peer.roomId) {
      return;
    }

    const snapshot = serializePeer(peer);
    const roomId = peer.roomId;
    closePeerMedia(peer, ws);
    removePeerFromRoom(peer);

    try {
      await postPresenceEvent(config, 'participant_left', peer);
    } catch (error) {
      console.error('participant_left callback failed', error);
    }

    peer.roomId = null;
    peer.callId = null;
    peer.callType = null;
    peer.userId = null;
    peer.sessionId = null;
    peer.tokenClaims = null;
    peer.joinedAt = null;
    peer.permissions = normalizePermissions();

    broadcastToRoom(roomId, ws, {
      event: eventName || 'peerLeft',
      data: snapshot
    });
  }

  function getObservabilitySummary() {
    const memory = process.memoryUsage();

    return {
      startedAt,
      uptimeSeconds: Math.round(process.uptime()),
      publicIp: config.publicIp,
      counts: {
        rooms: rooms.size,
        peers: peers.size,
        producers: producers.size
      },
      counters,
      process: {
        pid: process.pid,
        rss: memory.rss,
        heapUsed: memory.heapUsed,
        heapTotal: memory.heapTotal
      },
      ice: getIceConfiguration(config),
      rooms: [...rooms.keys()].map((roomId) => {
        const roomPeers = [...peers.values()].filter((peer) => peer.roomId === roomId);

        return {
          roomId,
          peerCount: roomPeers.length,
          producerCount: [...producers.values()].filter((info) => info.roomId === roomId)
            .length,
          consumerCount: roomPeers.reduce((sum, peer) => sum + peer.consumers.size, 0)
        };
      })
    };
  }

  function serializeRoomObservability(roomId) {
    const room = rooms.get(roomId);

    if (!room) {
      return null;
    }

    const roomPeers = [...peers.values()].filter((peer) => peer.roomId === roomId);
    const roomProducers = [...producers.entries()]
      .filter(([, info]) => info.roomId === roomId)
      .map(([producerId, info]) => serializeProducerInfo(producerId, info));

    return {
      roomId,
      peerCount: roomPeers.length,
      producerCount: roomProducers.length,
      consumerCount: roomPeers.reduce((sum, peer) => sum + peer.consumers.size, 0),
      peers: roomPeers.map(serializePeerObservability),
      producers: roomProducers
    };
  }

  app.use(express.json());

  app.get('/health', (_req, res) => {
    res.json({ ok: true });
  });

  app.get('/rtc-config', (_req, res) => {
    res.json(getIceConfiguration(config));
  });

  app.get('/observability/summary', (_req, res) => {
    res.json(getObservabilitySummary());
  });

  app.get('/observability/rooms/:roomId', (req, res) => {
    const roomId = String(req.params.roomId || '').trim();
    const snapshot = serializeRoomObservability(roomId);

    if (!snapshot) {
      return res.status(404).json({ error: 'room not found' });
    }

    res.json(snapshot);
  });

  server.on('upgrade', (request, socket, head) => {
    if (request.url !== config.wsPath) {
      socket.destroy();
      return;
    }

    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request);
    });
  });

  wss.on('connection', (ws) => {
    const peer = {
      id: `peer-${nextPeerNumber++}`,
      roomId: null,
      callId: null,
      callType: null,
      userId: null,
      sessionId: null,
      joinedAt: null,
      tokenClaims: null,
      permissions: normalizePermissions(),
      transportState: {
        send: null,
        recv: null
      },
      sendTransport: null,
      recvTransport: null,
      producers: new Map(),
      consumers: new Map()
    };

    peers.set(ws, peer);
    counters.wsConnectionsOpened += 1;

    send(ws, {
      event: 'connected',
      data: { peerId: peer.id }
    });

    ws.on('error', (error) => {
      console.error('websocket error', peer.id, error);
    });

    ws.on('message', async (raw) => {
      let msg;

      try {
        msg = JSON.parse(raw.toString());
        const { action, requestId, data = {} } = msg;
        const currentPeer = getPeer(ws);

        if (action === 'joinRoom') {
          const claims = verifyRtcToken(data.token, config.rtcJwtSecret);
          const roomId = String(claims.room_id).trim();

          if (currentPeer.roomId && currentPeer.roomId !== roomId) {
            await leaveCurrentRoom(currentPeer, ws, 'peerLeft');
          }

          currentPeer.roomId = roomId;
          currentPeer.callId = String(claims.call_id);
          currentPeer.callType = String(claims.call_type);
          currentPeer.userId = String(claims.user_id);
          currentPeer.sessionId = String(claims.session_id);
          currentPeer.joinedAt = new Date().toISOString();
          currentPeer.tokenClaims = claims;
          currentPeer.permissions = claims.permissions;

          const room = getOrCreateRoom(roomId);
          room.peerIds.add(currentPeer.id);

          try {
            await postPresenceEvent(config, 'participant_joined', currentPeer);
          } catch (error) {
            removePeerFromRoom(currentPeer);
            currentPeer.roomId = null;
            currentPeer.callId = null;
            currentPeer.callType = null;
            currentPeer.userId = null;
            currentPeer.sessionId = null;
            currentPeer.joinedAt = null;
            currentPeer.tokenClaims = null;
            currentPeer.permissions = normalizePermissions();
            throw error;
          }

          counters.roomJoins += 1;

          broadcastToRoom(roomId, ws, {
            event: 'peerJoined',
            data: serializePeer(currentPeer)
          });

          return send(ws, {
            requestId,
            ok: true,
            data: {
              roomId,
              callId: currentPeer.callId,
              callType: currentPeer.callType,
              peerId: currentPeer.id,
              userId: currentPeer.userId,
              sessionId: currentPeer.sessionId,
              permissions: currentPeer.permissions,
              participants: getRoomPeerSnapshots(roomId, currentPeer.id)
            }
          });
        }

        if (action === 'getRouterRtpCapabilities') {
          return send(ws, {
            requestId,
            ok: true,
            data: router.rtpCapabilities
          });
        }

        if (action === 'createWebRtcTransport') {
          ensureJoinedRoom(currentPeer);

          if (data.direction === 'recv') {
            ensureCanConsume(currentPeer);
          } else if (data.direction === 'send') {
            ensureCanSend(currentPeer);
          }

          const transport = await createWebRtcTransport();
          currentPeer.transportState[data.direction] = {
            id: transport.id,
            iceState: transport.iceState || null,
            dtlsState: transport.dtlsState || null
          };

          if (data.direction === 'send') {
            currentPeer.sendTransport = transport;
          } else if (data.direction === 'recv') {
            currentPeer.recvTransport = transport;
          } else {
            throw new Error('direction must be send or recv');
          }

          if (typeof transport.on === 'function') {
            transport.on('icestatechange', (state) => {
              currentPeer.transportState[data.direction].iceState = state;
            });
          }

          transport.on('dtlsstatechange', (state) => {
            currentPeer.transportState[data.direction].dtlsState = state;
            if (state === 'closed') {
              transport.close();
            }
          });

          return send(ws, {
            requestId,
            ok: true,
            data: serializeTransport(transport)
          });
        }

        if (action === 'connectTransport') {
          ensureJoinedRoom(currentPeer);
          const transport = getTransport(currentPeer, data.direction);

          if (!transport) {
            throw new Error(`transport not found for ${data.direction}`);
          }

          await transport.connect({
            dtlsParameters: data.dtlsParameters
          });

          return send(ws, {
            requestId,
            ok: true,
            data: { connected: true }
          });
        }

        if (action === 'produce') {
          ensureJoinedRoom(currentPeer);
          ensureCanSend(currentPeer);

          if (!currentPeer.sendTransport) {
            throw new Error('send transport not found');
          }

          const source = data.source || (data.kind === 'audio' ? 'microphone' : 'camera');
          ensureCanProduce(currentPeer, data.kind, source);

          const producer = await currentPeer.sendTransport.produce({
            kind: data.kind,
            rtpParameters: data.rtpParameters
          });
          counters.produces += 1;

          currentPeer.producers.set(producer.id, producer);
          producers.set(producer.id, {
            producer,
            peerId: currentPeer.id,
            userId: currentPeer.userId,
            roomId: currentPeer.roomId,
            callId: currentPeer.callId,
            kind: producer.kind,
            source
          });

          producer.on('transportclose', () => {
          producer.close();
        });

          producer.on('close', () => {
            const producerInfo = producers.get(producer.id);
            currentPeer.producers.delete(producer.id);

            if (producerInfo && currentPeer.roomId) {
              producers.delete(producer.id);
              broadcastToRoom(currentPeer.roomId, ws, {
                event: 'producerClosed',
                data: serializeProducerInfo(producer.id, producerInfo)
              });
            }
          });

          broadcastToRoom(currentPeer.roomId, ws, {
            event: 'producerAdded',
            data: serializeProducerInfo(producer.id, {
              peerId: currentPeer.id,
              userId: currentPeer.userId,
              roomId: currentPeer.roomId,
              callId: currentPeer.callId,
              kind: producer.kind,
              source
            })
          });

          return send(ws, {
            requestId,
            ok: true,
            data: { id: producer.id }
          });
        }

        if (action === 'getProducers') {
          ensureJoinedRoom(currentPeer);
          ensureCanConsume(currentPeer);

          const list = [];

          for (const [producerId, info] of producers.entries()) {
            if (info.roomId !== currentPeer.roomId) continue;
            if (info.peerId === currentPeer.id) continue;

            list.push(serializeProducerInfo(producerId, info));
          }

          return send(ws, {
            requestId,
            ok: true,
            data: list
          });
        }

        if (action === 'consume') {
          ensureJoinedRoom(currentPeer);
          ensureCanConsume(currentPeer);

          if (!currentPeer.recvTransport) {
            throw new Error('recv transport not found');
          }

          const producerInfo = producers.get(data.producerId);

          if (!producerInfo) {
            throw new Error('producer not found');
          }

          if (producerInfo.roomId !== currentPeer.roomId) {
            throw new Error('producer is not in your room');
          }

          if (
            !router.canConsume({
              producerId: data.producerId,
              rtpCapabilities: data.rtpCapabilities
            })
          ) {
            throw new Error('cannot consume this producer');
          }

          const consumer = await currentPeer.recvTransport.consume({
            producerId: data.producerId,
            rtpCapabilities: data.rtpCapabilities,
            paused: true
          });
          counters.consumes += 1;

          currentPeer.consumers.set(consumer.id, consumer);

          consumer.on('transportclose', () => {
            consumer.close();
          });

          consumer.on('producerclose', () => {
            currentPeer.consumers.delete(consumer.id);

            send(ws, {
              event: 'consumerClosed',
              data: {
                consumerId: consumer.id,
                producerId: data.producerId
              }
            });

            consumer.close();
          });

          const profileResult = await applyConsumerProfile(
            consumer,
            data.profile || 'high'
          );

          return send(ws, {
            requestId,
            ok: true,
            data: {
              id: consumer.id,
              producerId: data.producerId,
              kind: consumer.kind,
              rtpParameters: consumer.rtpParameters,
              type: consumer.type,
              profileResult
            }
          });
        }

        if (action === 'resumeConsumer') {
          const consumer = currentPeer.consumers.get(data.consumerId);

          if (!consumer) {
            throw new Error('consumer not found');
          }

          await consumer.resume();

          return send(ws, {
            requestId,
            ok: true,
            data: { resumed: true }
          });
        }

        if (action === 'setConsumerProfile') {
          const consumer = currentPeer.consumers.get(data.consumerId);

          if (!consumer) {
            throw new Error('consumer not found');
          }

          const profileResult = await applyConsumerProfile(
            consumer,
            data.profile || 'high'
          );

          return send(ws, {
            requestId,
            ok: true,
            data: profileResult
          });
        }

        if (action === 'leaveRoom') {
          await leaveCurrentRoom(currentPeer, ws, 'peerLeft');

          return send(ws, {
            requestId,
            ok: true,
            data: { left: true }
          });
        }

        return send(ws, {
          requestId,
          ok: false,
          error: `unknown action: ${action}`
        });
      } catch (error) {
        counters.errors += 1;
        send(ws, {
          requestId: msg?.requestId ?? null,
          ok: false,
          error: error.message
        });
      }
    });

    ws.on('close', () => {
      counters.wsConnectionsClosed += 1;
      leaveCurrentRoom(peer, ws, 'peerLeft').finally(() => {
        peers.delete(ws);
      });
    });
  });

  return server;
}

module.exports = {
  createRtcServer,
  getIceConfiguration
};
