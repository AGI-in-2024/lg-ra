OpenAI compatibility

Gemini models are accessible using the OpenAI libraries (Python and TypeScript / Javascript) along with the REST API, by updating three lines of code and using your Gemini API key. If you aren't already using the OpenAI libraries, we recommend that you call the Gemini API directly.

Python
JavaScript
REST

from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Explain to me how AI works"
        }
    ]
)

print(response.choices[0].message)
What changed? Just three lines!

api_key="GEMINI_API_KEY": Replace "GEMINI_API_KEY" with your actual Gemini API key, which you can get in Google AI Studio.

base_url="https://generativelanguage.googleapis.com/v1beta/openai/": This tells the OpenAI library to send requests to the Gemini API endpoint instead of the default URL.

model="gemini-2.0-flash": Choose a compatible Gemini model

Thinking
Gemini 2.5 models are trained to think through complex problems, leading to significantly improved reasoning. The Gemini API comes with a "thinking budget" parameter which gives fine grain control over how much the model will think.

Unlike the Gemini API, the OpenAI API offers three levels of thinking control: "low", "medium", and "high", which map to 1,024, 8,192, and 24,576 tokens, respectively.

If you want to disable thinking, you can set reasoning_effort to "none" (note that reasoning cannot be turned off for 2.5 Pro models).

Python
JavaScript
REST

from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.5-flash",
    reasoning_effort="low",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Explain to me how AI works"
        }
    ]
)

print(response.choices[0].message)
Gemini thinking models also produce thought summaries and can use exact thinking budgets. You can use the extra_body field to include these fields in your request.

Note that reasoning_effort and thinking_budget overlap functionality, so they can't be used at the same time.

Python
JavaScript
REST

from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[{"role": "user", "content": "Explain to me how AI works"}],
    extra_body={
      'extra_body': {
        "google": {
          "thinking_config": {
            "thinking_budget": 800,
            "include_thoughts": True
          }
        }
      }
    }
)

print(response.choices[0].message)
Streaming
The Gemini API supports streaming responses.

Python
JavaScript
REST

from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
  model="gemini-2.0-flash",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  stream=True
)

for chunk in response:
    print(chunk.choices[0].delta)
Function calling
Function calling makes it easier for you to get structured data outputs from generative models and is supported in the Gemini API.

Python
JavaScript
REST

from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

tools = [
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Get the weather in a given location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. Chicago, IL",
          },
          "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
        },
        "required": ["location"],
      },
    }
  }
]

messages = [{"role": "user", "content": "What's the weather like in Chicago today?"}]
response = client.chat.completions.create(
  model="gemini-2.0-flash",
  messages=messages,
  tools=tools,
  tool_choice="auto"
)

print(response)
Image understanding
Gemini models are natively multimodal and provide best in class performance on many common vision tasks.

Python
JavaScript
REST

import base64
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Getting the base64 string
base64_image = encode_image("Path/to/agi/image.jpeg")

response = client.chat.completions.create(
  model="gemini-2.0-flash",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is in this image?",
        },
        {
          "type": "image_url",
          "image_url": {
            "url":  f"data:image/jpeg;base64,{base64_image}"
          },
        },
      ],
    }
  ],
)

print(response.choices[0])
Generate an image
Note: Image generation is only available in the paid tier.
Generate an image:

Python
JavaScript
REST

import base64
from openai import OpenAI
from PIL import Image
from io import BytesIO

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

response = client.images.generate(
    model="imagen-3.0-generate-002",
    prompt="a portrait of a sheepadoodle wearing a cape",
    response_format='b64_json',
    n=1,
)

for image_data in response.data:
  image = Image.open(BytesIO(base64.b64decode(image_data.b64_json)))
  image.show()
Audio understanding
Analyze audio input:

Python
JavaScript
REST

import base64
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

with open("/path/to/your/audio/file.wav", "rb") as audio_file:
  base64_audio = base64.b64encode(audio_file.read()).decode('utf-8')

response = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Transcribe this audio",
        },
        {
              "type": "input_audio",
              "input_audio": {
                "data": base64_audio,
                "format": "wav"
          }
        }
      ],
    }
  ],
)

print(response.choices[0].message.content)
Structured output
Gemini models can output JSON objects in any structure you define.

Python
JavaScript

from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = client.beta.chat.completions.parse(
    model="gemini-2.0-flash",
    messages=[
        {"role": "system", "content": "Extract the event information."},
        {"role": "user", "content": "John and Susan are going to an AI conference on Friday."},
    ],
    response_format=CalendarEvent,
)

print(completion.choices[0].message.parsed)
Embeddings
Text embeddings measure the relatedness of text strings and can be generated using the Gemini API.

Python
JavaScript
REST

from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.embeddings.create(
    input="Your text string goes here",
    model="gemini-embedding-001"
)

print(response.data[0].embedding)
extra_body
There are several features supported by Gemini that are not available in OpenAI models but can be enabled using the extra_body field.

extra_body features

safety_settings	Corresponds to Gemini's SafetySetting.
cached_content	Corresponds to Gemini's GenerateContentRequest.cached_content.
thinking_config	Corresponds to Gemini's ThinkingConfig.
cached_content
Here's an example of using extra_body to set cached_content:

Python

from openai import OpenAI

client = OpenAI(
    api_key=MY_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

stream = client.chat.completions.create(
    model="gemini-2.5-pro",
    n=1,
    messages=[
        {
            "role": "user",
            "content": "Summarize the video"
        }
    ],
    stream=True,
    stream_options={'include_usage': True},
    extra_body={
        'extra_body':
        {
            'google': {
              'cached_content': "cachedContents/0000aaaa1111bbbb2222cccc3333dddd4444eeee"
          }
        }
    }
)

for chunk in stream:
    print(chunk)
    print(chunk.usage.to_dict())
List models
Get a list of available Gemini models:

Python
JavaScript
REST

from openai import OpenAI

client = OpenAI(
  api_key="GEMINI_API_KEY",
  base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

models = client.models.list()
for model in models:
  print(model.id)
Retrieve a model
Retrieve a Gemini model:

Python
JavaScript
REST

from openai import OpenAI

client = OpenAI(
  api_key="GEMINI_API_KEY",
  base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = client.models.retrieve("gemini-2.0-flash")
print(model.id)
Current limitations
Support for the OpenAI libraries is still in beta while we extend feature support.

If you have questions about supported parameters, upcoming features, or run into any issues getting started with Gemini, join our Developer Forum.

What's next
Try our OpenAI Compatibility Colab to work through more detailed examples.