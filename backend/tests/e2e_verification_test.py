import asyncio
import httpx
import websockets
import json
import sys

async def run_e2e_test():
    print("🚀 Starting Automated E2E Verification Test (Simulating Browser)...")
    ws_url = "ws://127.0.0.1:8000/ws/telemetry"
    api_url = "http://127.0.0.1:8000"
    
    print(f"🔗 Connecting to WebSocket at {ws_url}...")
    try:
        async with websockets.connect(ws_url) as websocket:
            print("📡 Connected successfully! Listening for telemetry and alerts...")
            
            # 1. First message from connection should be the initial alerts list
            init_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            init_data = json.loads(init_message)
            print(f"📥 Initial WebSocket Message: {init_data}")
            assert init_data["cmd"] == "alerts", "First command should be 'alerts'"
            
            offline_alert_id = None
            
            # 2. Wait to receive an offline alert
            print("⏳ Waiting for a drone to go offline (this can take up to 25s based on simulator intervals)...")
            while True:
                msg = await asyncio.wait_for(websocket.recv(), timeout=35.0)
                payload = json.loads(msg)
                
                if payload["cmd"] == "alerts":
                    alerts = payload["data"]
                    print(f"🚨 Received Alerts Update: {alerts}")
                    for alert in alerts:
                        if alert["type"] == "offline":
                            offline_alert_id = alert["id"]
                            print(f"🎯 FOUND Offline Alert! ID: {offline_alert_id}, Message: {alert['message']}")
                            break
                if offline_alert_id:
                    break
            
            # 3. Call REST API to dismiss the alert
            print(f"👉 Simulating User Click: Dismissing Alert {offline_alert_id} via API...")
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{api_url}/alerts/{offline_alert_id}/dismiss")
                print(f"📥 REST API Response: {res.status_code} - {res.json()}")
                assert res.status_code == 200, "REST API should return 200"
                assert res.json()["status"] == "success", "Response should be success"
            
            # 4. Wait for WebSocket update confirming the alert is dismissed
            print("⏳ Waiting for WebSocket to broadcast the updated alerts list (confirming dismissal)...")
            dismiss_confirmed = False
            for _ in range(5):
                msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                payload = json.loads(msg)
                if payload["cmd"] == "alerts":
                    alerts = payload["data"]
                    active_ids = [a["id"] for a in alerts]
                    print(f"🚨 Received Alerts Update after dismissal: {alerts}")
                    if offline_alert_id not in active_ids:
                        print("🎉 E2E Verification SUCCESS! Offline Alert has been successfully dismissed and cleared!")
                        dismiss_confirmed = True
                        break
            
            if not dismiss_confirmed:
                print("❌ E2E Verification FAILED: Alert was not cleared from WS broadcast.")
                sys.exit(1)
                
    except asyncio.TimeoutError:
        print("❌ E2E Verification FAILED: Timeout waiting for WebSocket message.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ E2E Verification FAILED with Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
