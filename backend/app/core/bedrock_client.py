import json

import boto3

from app.core.config import settings


def get_bedrock_client():
    """Create and return a Bedrock Runtime client."""
    kwargs = {
        "service_name": "bedrock-runtime",
        "region_name": settings.aws_region,
    }
    if settings.aws_bedrock_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_bedrock_endpoint_url
    return boto3.client(**kwargs)


async def invoke_model(prompt: str, max_tokens: int = 4096) -> str:
    """Invoke a Bedrock model and return the text response."""
    client = get_bedrock_client()

    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    )

    response = client.invoke_model(
        modelId=settings.aws_bedrock_model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())
    return response_body["content"][0]["text"]
