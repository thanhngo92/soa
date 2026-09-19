import httpx
from fastapi import Request, Response

STRIP_HEADERS = {"host", "content-length", "transfer-encoding", "connection"}


async def forward_request(http_client: httpx.AsyncClient, target_url: str, request: Request) -> Response:
    headers = {k: v for k, v in request.headers.items() if k.lower() not in STRIP_HEADERS}
    body = await request.body()

    try:
        upstream = await http_client.request(
            method=request.method,
            url=target_url,
            params=dict(request.query_params),
            headers=headers,
            content=body,
        )
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            media_type=upstream.headers.get("content-type", "application/json"),
        )
    except httpx.ConnectError:
        return Response(
            content='{"success":false,"error":{"code":"SERVICE_UNAVAILABLE","message":"Service unavailable"}}',
            status_code=502,
            media_type="application/json",
        )
    except httpx.TimeoutException:
        return Response(
            content='{"success":false,"error":{"code":"GATEWAY_TIMEOUT","message":"Gateway timeout"}}',
            status_code=504,
            media_type="application/json",
        )
