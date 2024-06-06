import java.io.IOException;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

public class InvertedIndexMapper extends Mapper<Object, Text, Text, Text> {

    private Text word = new Text();
    private Text location = new Text();

    @Override
    protected void map(Object key, Text value, Context context) throws IOException, InterruptedException {
        String fileName = ((org.apache.hadoop.mapreduce.lib.input.FileSplit) context.getInputSplit()).getPath().getName();
        String line = value.toString();
        String[] words = line.split("\\s+");
        for (int i = 0; i < words.length; i++) {
            word.set(words[i]);
            location.set(fileName + ":" + i);
            context.write(word, location);
        }
    }
}