CFLAGS=-I../src
LDFLAGS=-L../src -lvosk -ldl -lpthread -Wl,-rpath=../src

all: test_vosk test_vosk_speaker test_phone_results

test_vosk: test_vosk.o
	g++ $^ -o $@ $(LDFLAGS)

test_vosk_speaker: test_vosk_speaker.o
	g++ $^ -o $@ $(LDFLAGS)

test_phone_results: test_phone_results.o
	g++ $^ -o $@ $(LDFLAGS)
%.o: %.c
	g++ $(CFLAGS) -c -o $@ $<

clean:
	rm -f *.o *.a test_vosk test_vosk_speaker test_phone_results
