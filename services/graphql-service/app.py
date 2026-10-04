import os
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, FastAPI
import httpx
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import strawberry
from strawberry.fastapi import GraphQLRouter


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


init_telemetry("weather-graphql-service")
HTTPXClientInstrumentor().instrument()

WEATHER_REST_URL = os.getenv("WEATHER_REST_URL", "http://localhost:8003")


async def get_weather_rest_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(base_url=WEATHER_REST_URL) as client:
        yield client


async def get_context(
    weather_rest_client: Annotated[
        httpx.AsyncClient,
        Depends(get_weather_rest_client),
    ],
) -> dict[str, httpx.AsyncClient]:
    return {"weather_rest_client": weather_rest_client}


@strawberry.type
class Weather:
    city: str
    temperature: int
    condition: str


@strawberry.type
class Query:
    @strawberry.field
    async def weather(self, info: strawberry.Info, city: str) -> Weather | None:
        client: httpx.AsyncClient = info.context["weather_rest_client"]
        response = await client.get(f"/weather/{city}")
        response.raise_for_status()

        return Weather(**response.json())


schema = strawberry.Schema(query=Query)
graphql_router = GraphQLRouter(schema, context_getter=get_context)

app = FastAPI(title="Weather GraphQL Service")
app.include_router(graphql_router, prefix="/graphql")
FastAPIInstrumentor.instrument_app(app)
