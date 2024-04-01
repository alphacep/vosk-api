import org.vosk.Model;
import org.vosk.Recognizer;

import javax.sound.sampled.UnsupportedAudioFileException;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.TimeUnit;
import java.util.stream.IntStream; 
import java.util.stream.Collectors;

import org.junit.Test;
import org.junit.Assert;

public class DecoderMultiTest {

    private static List<InputStream> getTestFiles() {
        List<InputStream> testFiles = new ArrayList<>(5);
        for (int i = 0; i < 5; i++) {
            testFiles.add(DecoderMultiTest.class.getResourceAsStream("/warm-up/" + (i + 1) + ".wav"));
        }
        return testFiles;
    }

    @Test
    public void decoderMultiTest() throws IOException, UnsupportedAudioFileException, InterruptedException {

//        String pathToModel = "../../python/example/vosk-model-ru-0.53-private-0.1";
        String pathToModel = "../../python/example/vosk-model-small-ru";

        int nStreams = Runtime.getRuntime().availableProcessors();

        Model model = new Model(pathToModel);
        ExecutorService executor = Executors.newFixedThreadPool(nStreams);
        Map<String, AtomicInteger> results = new ConcurrentHashMap<>();

        IntStream.range(0, nStreams).mapToObj(it -> executor.submit(() -> {
            try {
                List<InputStream> testFiles = getTestFiles();
                for (int i = 0; i < testFiles.size(); i++) {
                    InputStream testFile = testFiles.get(i);
                    String file = "/warm-up/" + (i + 1) + ".wav";
                    Recognizer recognizer = new Recognizer(model, 8000.0f);
                    String result = recognize(recognizer, "rec file=" + file + " thread=" + Thread.currentThread().getName(), testFile);
                    results.computeIfAbsent(result, (resultString) -> new AtomicInteger()).incrementAndGet();
                }
             } catch (Exception e) {
                throw new RuntimeException(e);
                // Do nothing
             }
        })).collect(Collectors.toList());
        executor.shutdown();
        executor.awaitTermination(Long.MAX_VALUE, TimeUnit.MILLISECONDS);
        System.out.println("RESULTS:" + printMap(results));
    }

    private static String recognize(Recognizer recognizer, String name, InputStream ais) throws IOException, InterruptedException {
        try (ais) {
            int nbytes;
            byte[] b = new byte[4000];
            int i = 0;
            StringBuilder result = new StringBuilder();
            while ((nbytes = ais.read(b)) >= 0) {
                recognizer.acceptWaveForm(b, nbytes);    
                while (recognizer.getNumPendingResults() > 0) {
                    Thread.sleep(50);
                }
                while (!recognizer.getResultsEmpty()) {
                    System.out.println("Result [" + name + "] [i=" + i + "] - " + recognizer.getResult());                
                    result.append(recognizer.getResult());
                    result.append(' ');
                    recognizer.popResult();
                }
            }
            recognizer.flush();
            while (recognizer.getNumPendingResults() > 0) {
                Thread.sleep(50);
            }
            while (!recognizer.getResultsEmpty()) {
                System.out.println("Result [" + name + "] [i=" + i + "] - " + recognizer.getResult());                
                result.append(recognizer.getResult());
                result.append(' ');
                recognizer.popResult();
            }

            return result.toString();
        }
    }

    private static String printMap(Map<?, ?> map) {
        StringBuilder sb = new StringBuilder();
        Iterator<? extends Map.Entry<?, ?>> iter = map.entrySet().iterator();
        while (iter.hasNext()) {
            Map.Entry<?, ?> entry = iter.next();
            sb.append(entry.getKey());
            sb.append('=').append('"');
            sb.append(entry.getValue());
            sb.append('"');
            if (iter.hasNext()) {
                sb.append(',').append('\n');
            }
        }
        return sb.toString();
    }
}
