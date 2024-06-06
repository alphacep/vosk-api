CFLAGS=-I../../src
LDFLAGS=-L../../src -lvosk -ldl -lpthread -Wl,-rpath,../../src

all: test_vosk test_vosk_multi

test_vosk: test_vosk.o
	gcc $^ -o $@ $(LDFLAGS)

test_vosk_multi: test_vosk_multi.o
	gcc $^ -o $@ $(LDFLAGS) -lpthread

%.o: %.c
	gcc $(CFLAGS) -c -o $@ $<

clean:
	rm -f *.o *.a test_vosk test_vosk_multi
