#include <vosk_api.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>

int main(int argc, char *argv[]) {
	if(argc == 1) {
		printf("missing .mp4 filename\n");
		return 0;
	}
	int p[2];
	pid_t pid;
	char data[4000];

	VoskModel *model = vosk_model_new("model");
	VoskRecognizer *recognizer = vosk_recognizer_new(model, 16000.0);
	vosk_recognizer_set_words(recognizer, 1);
	int final;

	if (pipe(p)==-1)
		fprintf(stderr, "%s\n", "pipe error"); 

	if ((pid = fork()) == -1)
		fprintf(stderr, "%s\n", "fork error"); 

	if(pid == 0) {
		dup2(p[1], STDOUT_FILENO); 
		close(p[0]);
		close(p[1]);
		execl("/usr/bin/ffmpeg", "ffmpeg", "-loglevel", "quiet", 
			"-i", argv[1], "-ar", "16000", "-ac", "1", "-f", "s16le", "-", NULL);
		perror("error:");
	} 
	else {
		close(p[1]);
		int nbytes; 
		//printf("Output: %s\n", data);

		while ((nbytes = read(p[0], data, sizeof(data))) != 0){
			final = vosk_recognizer_accept_waveform(recognizer, data, nbytes); 
			if (final) {
				printf("%s\n", vosk_recognizer_result(recognizer));
			}
			else {
				printf("%s\n", vosk_recognizer_partial_result(recognizer));
			}
		}

		printf("%s\n", vosk_recognizer_final_result(recognizer));
		vosk_recognizer_free(recognizer);
		vosk_model_free(model);
		wait(NULL);
	}

	return 0;
}
