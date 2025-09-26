package Bad.Pkg.Name;

import java.util.*;

public class Demo {

    public String url = "http://example.com";
    public static String Id = "xyz";

    public List<String> toUpper(List<String> input) {
        List<String> res = new ArrayList<>();
        for (String s : input) {
            res.add(s.toUpperCase());
        }
        return res;
    }

    static class Holder {
        List<Integer> numbers;
        Holder(List<Integer> n) { this.numbers = n; }
        public List<Integer> getNumbers() { return numbers; }
    }

    public void risky(Stack<String> stack) {
        try {
            stack.pop();
        } catch (Exception e) {
            e.printStackTrace();
        } catch (EmptyStackException ee) {
            System.out.println("never here");
        }
    }

    public Vector<Integer> vec() {
        Vector<Integer> v = new Vector<>();
        v.add(1);
        return v;
    }

    public void compute() { helper(); }
    public void helper() {}

    public ArrayList<Integer> ids() { return new ArrayList<>(); }

    interface OnlyOne {
        void run();
    }
    static class OnlyOneImpl implements OnlyOne {
        public void run() {}
    }

    static class Key {
        int id;
        Key(int i) { id = i; }
        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof Key)) return false;
            return id == ((Key) o).id;
        }
    }

    public static void main(String[] args) {
        Demo d = new Demo();
        d.toUpper(Arrays.asList("a","b"));
    }
}
