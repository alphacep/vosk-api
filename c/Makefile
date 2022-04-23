CFLAGS=-I../src
LDFLAGS=-L../src -lvosk -ldl -lpthread -Wl,-rpath=../src

all: test_vosk test_vosk_speaker

test_vosk: test_vosk.o
	$(CXX) $^ -o $@ $(LDFLAGS)

test_vosk_speaker: test_vosk_speaker.o
	$(CXX) $^ -o $@ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f *.o *.a test_vosk test_vosk_speaker
