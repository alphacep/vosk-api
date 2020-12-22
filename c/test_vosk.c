#include <vosk_api.h>
#include <stdio.h>

int main() {
    FILE *wavin;
    char buf[3200];
    int nread, final;

    VoskModel *model = vosk_model_new("model");
    VoskRecognizer *recognizer = vosk_recognizer_new(model, 16000.0);

    wavin = fopen("test.wav", "rb");
    fseek(wavin, 44, SEEK_SET);
    while (!feof(wavin)) {
         nread = fread(buf, 1, sizeof(buf), wavin);
         final = vosk_recognizer_accept_waveform(recognizer, buf, nread);
         if (final) {
             printf("%s\n", vosk_recognizer_result(recognizer));
         } else {
             printf("%s\n", vosk_recognizer_partial_result(recognizer));
         }
    }
    printf("%s\n", vosk_recognizer_final_result(recognizer));

    vosk_recognizer_free(recognizer);
    vosk_model_free(model);
    fclose(wavin);
    return 0;
}
