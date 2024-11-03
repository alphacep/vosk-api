#include <vosk_api.h>
#include <stdio.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>

#define NUM_THREADS 10
#define NUM_FILES_PER_THREAD 3
#define NUM_FILES 400
#define MAX_FILE 100

VoskModel *model;
char infiles[NUM_FILES][MAX_FILE];
pthread_t thread_ids[NUM_THREADS];

static void *worker(void *data) {
    int j;

    for (j = 0; j < NUM_FILES_PER_THREAD; j++) {
        FILE *wavin;
        char buf[4000];
        int nread;
        VoskRecognizer *recognizer = vosk_recognizer_new(model, 16000.0);
        int foffset = rand() % NUM_FILES;

        wavin = fopen(infiles[foffset], "rb");
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
        fclose(wavin);
    }
}

void read_file_list() {
    FILE* infile;
    infile = fopen("file.list", "r");
    int i = 0;

    while(i < NUM_FILES, fgets(infiles[i], MAX_FILE, infile)) {
        infiles[i][strlen(infiles[i]) - 1] = 0;
        printf("%s\n", infiles[i]);
        i++;
    }

    fclose(infile);
}

int main() {
    int i;
    srand(0);

    read_file_list();

    model = vosk_model_new("vosk-model-small-ru");
    for (i = 0; i < NUM_THREADS; i++) {
        pthread_create(&thread_ids[i], NULL, worker, NULL);
    }
    for (i = 0; i < NUM_THREADS; i++) {
        pthread_join(thread_ids[i], NULL);
    }
    vosk_model_free(model);
    return 0;
}
