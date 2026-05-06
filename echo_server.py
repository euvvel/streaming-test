"""
Streaming test echo server.
Sends response in 3 chunks with deliberate delays.
Accepts multiple connections.

Listens on: 0.0.0.0:8080
Cloudflare tunnel forwards to this port.
"""

import socket
import time
import threading

HOST = '0.0.0.0'
PORT = 8080

def handle_client(conn, addr):
    print(f"\n[echo] === Connection from {addr} ===", flush=True)
    try:
        conn.settimeout(30)
        
        # Read the request body (from Apps Script)
        data = conn.recv(65536)
        if not data:
            print(f"[echo] No data received", flush=True)
            return
        
        text = data.decode('utf-8', errors='replace')
        print(f"[echo] Received {len(data)} bytes", flush=True)
        print(f"[echo] Content: {text[:150]}", flush=True)
        
        # Send response as HTTP so UrlFetchApp handles it properly
        # Apps Script's UrlFetchApp expects HTTP responses
        body_chunk1 = f"CHUNK1:{time.time()}\n"
        
        # Send HTTP headers + first chunk immediately
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            "Transfer-Encoding: chunked\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        conn.sendall(headers.encode())
        print(f"[echo] Sent HTTP headers", flush=True)
        
        # Chunked encoding: send chunk size in hex, then data, then CRLF
        chunk1_hex = f"{len(body_chunk1):x}\r\n"
        conn.sendall(chunk1_hex.encode())
        conn.sendall(body_chunk1.encode())
        conn.sendall(b"\r\n")
        print(f"[echo] Sent CHUNK1 at {time.time()}", flush=True)
        
        # Delay 3 seconds before CHUNK2
        print(f"[echo] Sleeping 3 seconds...", flush=True)
        time.sleep(3)
        
        body_chunk2 = f"CHUNK2:{time.time()}\n"
        chunk2_hex = f"{len(body_chunk2):x}\r\n"
        conn.sendall(chunk2_hex.encode())
        conn.sendall(body_chunk2.encode())
        conn.sendall(b"\r\n")
        print(f"[echo] Sent CHUNK2 at {time.time()}", flush=True)
        
        # Delay 3 more seconds before CHUNK3
        print(f"[echo] Sleeping 3 seconds...", flush=True)
        time.sleep(3)
        
        body_chunk3 = f"CHUNK3:{time.time()}\n"
        chunk3_hex = f"{len(body_chunk3):x}\r\n"
        conn.sendall(chunk3_hex.encode())
        conn.sendall(body_chunk3.encode())
        conn.sendall(b"\r\n")
        print(f"[echo] Sent CHUNK3 at {time.time()}", flush=True)
        
        # Final chunk (zero-length = end of chunked response)
        conn.sendall(b"0\r\n\r\n")
        print(f"[echo] Sent final chunk (end of response)", flush=True)
        
        # Brief pause so client reads everything
        time.sleep(1)
        
    except socket.timeout:
        print(f"[echo] Timeout waiting for data", flush=True)
    except Exception as e:
        print(f"[echo] Error: {e}", flush=True)
    finally:
        conn.close()
        print(f"[echo] Connection closed", flush=True)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)
    
    print(f"[echo] Server listening on {HOST}:{PORT}", flush=True)
    print(f"[echo]", flush=True)
    print(f"[echo] This server responds to HTTP requests with chunked encoding:", flush=True)
    print(f"[echo]   CHUNK1: immediately after headers", flush=True)
    print(f"[echo]   CHUNK2: after 3 second delay", flush=True)
    print(f"[echo]   CHUNK3: after 6 second delay", flush=True)
    print(f"[echo]", flush=True)
    print(f"[echo] If Apps Script streams: client sees chunks arrive over ~6s", flush=True)
    print(f"[echo] If Apps Script buffers: client gets everything at once after ~8s", flush=True)
    print(f"[echo]", flush=True)
    
    connection_count = 0
    while True:
        try:
            conn, addr = sock.accept()
            connection_count += 1
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
        except KeyboardInterrupt:
            print(f"\n[echo] Shutting down (served {connection_count} connections)", flush=True)
            break
        except Exception as e:
            print(f"[echo] Accept error: {e}", flush=True)
            break

if __name__ == '__main__':
    main()
