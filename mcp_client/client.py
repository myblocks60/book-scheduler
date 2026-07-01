import urllib.request
import urllib.parse
import json
import ssl
import time

def call_mcp_tool(userid: str, firmid: str, provider: str = None) -> list:
    """
    Connects to the MCP SSE server, retrieves a sessionId, calls list_api_keys,
    and listens for the response over the event stream.
    """
    sse_url = "https://myblocks.in:3100/sse"
    messages_base = "https://myblocks.in:3100"
    
    # Create SSL context that ignores certificate validation if needed (common for dev/local self-signed)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        sse_url,
        headers={"Accept": "text/event-stream", "User-Agent": "FastAPI-MCP-Client"}
    )
    
    session_id = None
    post_url = None
    result = None
    
    # Establish connection
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            # We must read line-by-line as it's an event stream
            line_buffer = []
            current_event = None
            
            for line_bytes in response:
                line = line_bytes.decode('utf-8').strip()
                if not line:
                    # Empty line indicates end of an event block
                    if line_buffer:
                        data_content = "".join(line_buffer)
                        if current_event == "endpoint":
                            # E.g. data_content is "/messages?sessionId=xxx" or full URL
                            if "sessionId=" in data_content:
                                parsed = urllib.parse.urlparse(data_content)
                                query = urllib.parse.parse_qs(parsed.query)
                                session_id = query.get("sessionId", [None])[0]
                                if data_content.startswith("http"):
                                    post_url = data_content
                                  
                                else:
                                    post_url = f"{messages_base}{data_content}"
                        
                        elif current_event == "message":
                            try:
                                msg_data = json.loads(data_content)
                                if msg_data.get("id") == 1:
                                    result = msg_data
                                    break
                            except Exception as parse_err:
                                print("Error parsing SSE message JSON:", parse_err)
                                
                        line_buffer = []
                        current_event = None
                    continue
                
                if line.startswith("event:"):
                    current_event = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    line_buffer.append(line[len("data:"):].strip())
                
                # Once session_id is found, we trigger the POST request in the background/sequentially
                if session_id and not post_url:
                    post_url = f"{messages_base}/messages?sessionId={session_id}"
                
                if post_url and result is None and len(line_buffer) == 0:
                    # Send the POST request to call the tool
                    payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": "list_api_keys",
                            "arguments": {
                                "userid": str(userid),
                                "firmid": str(firmid)
                            }
                        }
                    }
                    if provider:
                        payload["params"]["arguments"]["provider"] = provider
                        
                    post_data = json.dumps(payload).encode('utf-8')
                    post_req = urllib.request.Request(
                        post_url,
                        data=post_data,
                        headers={"Content-Type": "application/json", "User-Agent": "FastAPI-MCP-Client"}
                    )
                    try:
                        # Send POST request
                        with urllib.request.urlopen(post_req, context=ctx, timeout=10) as post_res:
                            post_res.read() # Consume response
                    except Exception as post_err:
                        print("Error sending tool call POST:", post_err)
                        break
                    
                    # Reset post_url so we don't send multiple POSTs
                    post_url = None
                    
            if result:
                # Extract results content
                try:
                    content_list = result.get("result", {}).get("content", [])
                    if content_list and content_list[0].get("type") == "text":
                        return json.loads(content_list[0].get("text", "[]"))
                except Exception as ext_err:
                    print("Error extracting content from result:", ext_err)
                    
    except Exception as e:
        print("MCP Connection Error:", e)
        
    return []
