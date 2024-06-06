import org.vosk.Model;
import org.vosk.Recognizer;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.Random;
import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.FileReader;

import org.junit.Test;
import org.junit.Assert;

public class DecoderMultiTest {

    private static ArrayList<String> getTestFiles() throws IOException {
        ArrayList<String> testFiles = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader("../../python/example/file.list"))) {
            String line;
            while ((line = br.readLine()) != null) {
                testFiles.add("../../python/example/" + line);
            }
        }
        return testFiles;
    }

    @Test
    public void decoderMultiTest() throws IOException, InterruptedException {

//        String pathToModel = "../../python/example/vosk-model-ru-0.53-private-0.1";
        String pathToModel = "../../python/example/vosk-model-small-ru";

        int nStreams = 30;
        int nAttempts = 4;

        Model model = new Model(pathToModel);
        ExecutorService executor = Executors.newFixedThreadPool(nStreams);
        ArrayList<String> testFiles = getTestFiles();

        IntStream.range(0, nStreams).mapToObj(it -> executor.submit(() -> {
            try {
                Random rnd = new Random();        
                for (int j = 0; j < nAttempts; j++) {
                    String testFile = testFiles.get(rnd.nextInt(testFiles.size()));
                    Recognizer recognizer = new Recognizer(model, 8000.0f);
                    recognize(recognizer, "rec file=" + testFile + " thread=" + Thread.currentThread().getName(), testFile);
               }
             } catch (Exception e) {
                throw new RuntimeException(e);
                // Do nothing
             }
        })).collect(Collectors.toList());
        executor.shutdown();
        executor.awaitTermination(Long.MAX_VALUE, TimeUnit.MILLISECONDS);
    }

    private static void recognize(Recognizer recognizer, String name, String inputFile) throws IOException, InterruptedException {
        FileInputStream ais = new FileInputStream(inputFile);
        int nbytes;
        byte[] b = new byte[4000];
        while ((nbytes = ais.read(b)) >= 0) {
            recognizer.acceptWaveForm(b, nbytes);
            while (recognizer.getNumPendingResults() > 0) {
                Thread.sleep(50);
            }
            while (!recognizer.getResultsEmpty()) {
                System.out.println("Result [" + name + "] " + recognizer.getResult());                
                recognizer.popResult();
            }
        }
        recognizer.flush();
        while (recognizer.getNumPendingResults() > 0) {
            Thread.sleep(50);
        }
        while (!recognizer.getResultsEmpty()) {
            System.out.println("Result [" + name + "] " + recognizer.getResult());
            recognizer.popResult();
        }
        return;
    }
}
