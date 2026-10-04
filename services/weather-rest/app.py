import os
from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel


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


init_telemetry("weather-rest-service")

app = FastAPI(title="Weather REST API")
FastAPIInstrumentor.instrument_app(app)


class Weather(BaseModel):
    city: str
    temperature: int
    condition: str


WEATHER_DATA = {
    "ha noi": Weather(city="Ha Noi", temperature=28, condition="Cloudy"),
    "da nang": Weather(city="Da Nang", temperature=30, condition="Sunny"),
    "ho chi minh city": Weather(
        city="Ho Chi Minh City",
        temperature=32,
        condition="Partly Cloudy",
    ),
}


def normalize_city(city: str) -> str:
    return " ".join(city.split()).casefold()


@app.get("/weather/{city}", response_model=Weather)
def get_weather(city: str) -> Weather:
    weather = WEATHER_DATA.get(normalize_city(city))
    if weather is None:
        raise HTTPException(
            status_code=404,
            detail=f"Weather data not found for city: {city}",
        )

    return weather
