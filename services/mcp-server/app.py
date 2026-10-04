import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_telemetry(service_name: str) -> None:
    resource = Resource.create({SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", service_name)})
    provider = TracerProvider(resource=resource)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        endpoint = (
            otlp_endpoint
            if otlp_endpoint.endswith("/v1/traces")
            else f"{otlp_endpoint.rstrip('/')}/v1/traces"
        )
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


init_telemetry("weather-mcp-server")
HTTPXClientInstrumentor().instrument()
tracer = trace.get_tracer("weather-mcp-server")

GRAPHQL_URL = os.getenv("GRAPHQL_URL", "http://localhost:8002/graphql")

GET_WEATHER_QUERY = """
query GetWeather($city: String!) {
  weather(city: $city) {
    city
    temperature
    condition
  }
}
"""


class WeatherResult(TypedDict):
    city: str
    temperature: int
    condition: str


@asynccontextmanager
async def get_graphql_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient() as client:
        yield client


mcp = MCPServer("Weather MCP Server")


@mcp.tool()
async def get_weather(city: str) -> WeatherResult:
    """Get weather information for a city."""
    with tracer.start_as_current_span("get_weather") as span:
        span.set_attribute("weather.city", city)
        try:
            async with get_graphql_client() as client:
                response = await client.post(
                    GRAPHQL_URL,
                    json={
                        "query": GET_WEATHER_QUERY,
                        "variables": {"city": city},
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ToolError("GraphQL service request failed.") from exc

        payload = response.json()
        if payload.get("errors"):
            raise ToolError(f"Weather lookup failed for city {city!r}.")

        weather = (payload.get("data") or {}).get("weather")
        if weather is None:
            raise ToolError(f"No weather data found for city {city!r}.")

        return {
            "city": weather["city"],
            "temperature": weather["temperature"],
            "condition": weather["condition"],
        }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        json_response=True,
        stateless_http=True,
    )
