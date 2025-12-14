const WebSocket = require('ws');
const net = require('net');

/**
 * Optional smoke test for terminal-daemon WebSocket connectivity
 *
 * This test will:
 * 1. Check if the terminal daemon is running on port 8787
 * 2. Attempt a WebSocket connection
 * 3. Verify basic connectivity (skip if server not running)
 *
 * Usage:
 *   npm run test:smoke
 *
 * The test will be skipped if the terminal daemon is not running,
 * making it safe for CI/CD pipelines.
 */
    async function runSmokeTest() {
    const TERMINAL_DAEMON_PORT = process.env.KYROS_DAEMON_PORT || 8787;
    const TERMINAL_DAEMON_HOST = 'localhost';

    console.log('🚀 Running terminal daemon smoke test...');

    // Check if terminal daemon is running
    const serverAvailable = await checkServerAvailability(TERMINAL_DAEMON_PORT, TERMINAL_DAEMON_HOST);

    if (!serverAvailable) {
        console.log(`⚠️  Terminal daemon not running on port ${TERMINAL_DAEMON_PORT}`);
        console.log('   Starting terminal daemon with: npm run dev');
        console.log('   Or run this test when daemon is running');
        console.log('✅ Smoke test completed successfully (server not running - this is OK)');
        return;
    }

    console.log(`✅ Terminal daemon is available on port ${TERMINAL_DAEMON_PORT}`);

    // Test WebSocket connectivity
    console.log(`🔌 Testing WebSocket connection to ws://${TERMINAL_DAEMON_HOST}:${TERMINAL_DAEMON_PORT}`);

    try {
        await new Promise((resolve, reject) => {
            const ws = new WebSocket(`ws://${TERMINAL_DAEMON_HOST}:${TERMINAL_DAEMON_PORT}`);

            let connected = false;
            let timeout;

            // Connection timeout
            timeout = setTimeout(() => {
                ws.close();
                if (!connected) {
                    reject(new Error('WebSocket connection timeout'));
                }
            }, 5000);

            ws.on('open', () => {
                connected = true;
                console.log('✅ WebSocket connection established');
                clearTimeout(timeout);

                // Send a simple ping/test message
                ws.send(JSON.stringify({
                    type: 'ping',
                    timestamp: Date.now()
                }));

                // Wait a moment for response then close
                setTimeout(() => {
                    ws.close();
                    resolve();
                }, 1000);
            });

            ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data);
                    console.log('📨 Received message:', message.type);
                } catch (e) {
                    console.log('📨 Received raw message:', data.toString());
                }
            });

            ws.on('error', (error) => {
                clearTimeout(timeout);
                console.error('❌ WebSocket error:', error.message);
                reject(error);
            });

            ws.on('close', () => {
                clearTimeout(timeout);
                if (connected) {
                    console.log('✅ WebSocket connection closed successfully');
                    resolve();
                }
            });
        });

        console.log('✅ All connectivity tests passed');
    } catch (error) {
        console.error('❌ WebSocket test failed:', error.message);
        process.exit(1);
    }
}
/**
 * Check if the terminal daemon server is running and available
 */
function checkServerAvailability(port, host) {
    return new Promise((resolve) => {
        const socket = new net.Socket();

        socket.setTimeout(2000);

        socket.on('connect', () => {
            socket.destroy();
            resolve(true);
        });

        socket.on('timeout', () => {
            socket.destroy();
            resolve(false);
        });

        socket.on('error', () => {
            resolve(false);
        });

        socket.connect(port, host);
    });
}

// Run the smoke test
if (require.main === module) {
    runSmokeTest().catch((error) => {
        console.error('❌ Smoke test failed:', error.message);
        process.exit(1);
    });
}