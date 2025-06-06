# Vosk + Spring Boot Application Demo

## Description:

A minimal example demonstrating the interaction between Spring Boot and the Vosk library.
Spring Boot version - 3.5.0

### Interaction Example

For testing purposes, the example directory contains a Postman collection and a test file.

The response is returned in the following format:

```
POST /api/detect
Request Params: wav and wavSize
```

```json
[
  {
    "data": "{\n  \"text\" : \"one zero zero zero one nine oh two i no zero one eight zero three\"\n}"
  }
]
```