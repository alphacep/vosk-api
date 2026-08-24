#include <vosk_api.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>

int main() {
    FILE *wavin;
    char buf[3200];
    int nread, final;

    vosk_gpu_init();
    VoskBatchModel *model = vosk_batch_model_new("model");
    VoskBatchRecognizer *recognizer = vosk_batch_recognizer_new(model, 16000.0);

    wavin = fopen("test.wav", "rb");
    fseek(wavin, 44, SEEK_SET);
    while (!feof(wavin)) {
         nread = fread(buf, 1, sizeof(buf), wavin);
         vosk_batch_recognizer_accept_waveform(recognizer,buf,nread);
         while(vosk_batch_recognizer_get_pending_chunks(recognizer)>0) usleep(1000);

         const char *result=vosk_batch_recognizer_front_result(recognizer);
         if(strlen(result)) {
             printf("%s\n", result);
             vosk_batch_recognizer_pop(recognizer);
         } else {
             printf("%s\n", vosk_batch_recognizer_partial_result(recognizer));
         }
    }

    fclose(wavin);
    vosk_batch_recognizer_free(recognizer);
    vosk_batch_model_free(model);
    return 0;
}
