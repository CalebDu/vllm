# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
import asyncio
import json

import httpx
from openai import OpenAI

from vllm.assets.audio import AudioAsset


def sync_openai(audio_path: str, client: OpenAI):
    with open(audio_path, "rb") as f:
        translation = client.audio.translations.create(
            file=f,
            model="openai/whisper-large-v3",
            response_format="json",
            temperature=0.0,
            # Additional params not provided by OpenAI API.
            extra_body=dict(
                language="it",
                seed=4419,
                repetition_penalty=1.3,
            ),
        )
        print("translation result:", translation.text)


async def stream_openai_response(audio_path: str, base_url: str, api_key: str):
    data = {
        "language": "it",
        "stream": True,
        "model": "openai/whisper-large-v3",
    }
    url = base_url + "/audio/translations"
    headers = {"Authorization": f"Bearer {api_key}"}
    print("translation result:", end=" ")
    # OpenAI translation API client does not support streaming.
    async with httpx.AsyncClient() as client:
        with open(audio_path, "rb") as f:
            async with client.stream(
                "POST", url, files={"file": f}, data=data, headers=headers
            ) as response:
                async for line in response.aiter_lines():
                    # Each line is a JSON object prefixed with 'data: '
                    if line:
                        if line.startswith("data: "):
                            line = line[len("data: ") :]
                        # Last chunk, stream ends
                        if line.strip() == "[DONE]":
                            break
                        # Parse the JSON response
                        chunk = json.loads(line)
                        # Extract and print the content
                        content = chunk["choices"][0].get("delta", {}).get("content")
                        print(content, end="")


def main():
    foscolo = str(AudioAsset("azacinto_foscolo").get_local_path())

    # Modify OpenAI's API key and API base to use vLLM's API server.
    openai_api_key = "EMPTY"
    openai_api_base = "http://localhost:8000/v1"
    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
    )
    sync_openai(foscolo, client)
    # Run the asynchronous function
    asyncio.run(stream_openai_response(foscolo, openai_api_base, openai_api_key))


if __name__ == "__main__":
    main()
