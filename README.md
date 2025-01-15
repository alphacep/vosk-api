# Vosk Speech Recognition Toolkit

Vosk is an offline open source speech recognition toolkit. It enables
speech recognition for 20+ languages and dialects - English, Indian
English, German, French, Spanish, Portuguese, Chinese, Russian, Turkish,
Vietnamese, Italian, Dutch, Catalan, Arabic, Greek, Farsi, Filipino,
Ukrainian, Kazakh, Swedish, Japanese, Esperanto, Hindi, Czech, Polish.
More to come.

Vosk models are small (50 Mb) but provide continuous large vocabulary
transcription, zero-latency response with streaming API, reconfigurable
vocabulary and speaker identification.

Speech recognition bindings implemented for various programming languages
like Python, Java, Node.JS, C#, C++, Rust, Go and others.

Vosk supplies speech recognition for chatbots, smart home appliances,
virtual assistants. It can also create subtitles for movies,
transcription for lectures and interviews.

Vosk scales from small devices like Raspberry Pi or Android smartphone to
big clusters.

# Documentation

For installation instructions, examples and documentation visit [Vosk
Website](https://alphacephei.com/vosk).

# Building and Running the Docker Container

To build the Docker container for the Gradio app, use the following command:

```sh
docker build -t gradio-app .
```

To run the Docker container, use the following command:

```sh
docker run -p 7860:7860 gradio-app
```

# Deploying the Container Using a Cloud Service

To deploy the Docker container using a cloud service like AWS or Heroku, follow the instructions provided by the respective service. For example, to deploy on Heroku, you can use the following steps:

1. Install the Heroku CLI and log in to your Heroku account.
2. Create a new Heroku app:
   ```sh
   heroku create
   ```
3. Push the Docker image to Heroku:
   ```sh
   heroku container:push web
   ```
4. Release the Docker image:
   ```sh
   heroku container:release web
   ```
5. Open the app in your browser:
   ```sh
   heroku open
   ```
