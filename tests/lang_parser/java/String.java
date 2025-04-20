public class String {
    public static void main(String []args) {
		java.lang.String blog = "blog.didispace.com";
		java.lang.String test = "asfa";
		java.lang.String str = STR."My blog is \{blog + test}!";
		// String[] searchList = {"{name}", "{age}"};
		// String[] replacementList = {name, String.valueOf(age)};
		// String greeting = StringUtils.replaceEach(template, searchList, replacementList);
		System.out.println(str);  // 输出: Hello, my name is Alice and I am 30 years old.
    }
}