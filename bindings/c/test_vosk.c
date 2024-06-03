#include <vosk_api.h>
#include <stdio.h>
#include <unistd.h>

int main() {
    FILE *wavin;
    char buf[3200];
    int nread, final;

    VoskModel *model = vosk_model_new("vosk-model-small-ru");
    VoskRecognizer *recognizer = vosk_recognizer_new(model, 16000.0);

    wavin = fopen("test.wav", "rb");
    fseek(wavin, 44, SEEK_SET);
    while (!feof(wavin)) {
         nread = fread(buf, 1, sizeof(buf), wavin);
         vosk_recognizer_accept_waveform(recognizer, buf, nread);
         while (vosk_recognizer_get_num_pending_results(recognizer) > 0)
             sleep(0.05);
         while (!vosk_recognizer_results_empty(recognizer)) {
             printf("%s\n", vosk_recognizer_result_front(recognizer));
             vosk_recognizer_result_pop(recognizer);
         }
    }
    vosk_recognizer_flush(recognizer);
    while (vosk_recognizer_get_num_pending_results(recognizer) > 0)
         sleep(0.05);
    while (!vosk_recognizer_results_empty(recognizer)) {
         printf("%s\n", vosk_recognizer_result_front(recognizer));
         vosk_recognizer_result_pop(recognizer);
    }

    vosk_recognizer_free(recognizer);
    vosk_model_free(model);
    fclose(wavin);
    return 0;
}
